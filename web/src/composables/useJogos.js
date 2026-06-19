import { ref, computed, watch } from 'vue'
import { useAuth } from './useAuth.js'
import { fetchJogos, fetchAllPalpites, fetchPalpites, savePalpite as apiSave } from '../api.js'
import { GAMES } from '../data/mock.js' // fallback

const jogos = ref([])
const palpitesMap = ref({}) // match_id -> { goalsA, goalsB }
const filtro = ref('abertos')
const loaded = ref(false)

export function useJogos() {
  const { user, telegramId, isLoggedIn } = useAuth()

  // Load real data when logged in
  watch(isLoggedIn, async (val) => {
    if (!val || loaded.value) return
    try {
      const [j, p] = await Promise.all([
        fetchJogos(),
        telegramId.value ? fetchPalpites(telegramId.value) : fetchAllPalpites(),
      ])
      jogos.value = j
      const map = {}
      for (const pal of p) {
        map[pal.match_id] = { goalsA: Number(pal.gols_casa), goalsB: Number(pal.gols_fora) }
      }
      palpitesMap.value = map
      loaded.value = true
    } catch (e) {
      console.warn('BigBase fetch failed, using mock data:', e.message)
      // Fallback to mock
      jogos.value = [...GAMES]
      import('../data/mock.js').then(({ PALPITES_SALVOS }) => {
        palpitesMap.value = { ...PALPITES_SALVOS }
        loaded.value = true
      })
    }
  })

  const jogosEnriquecidos = computed(() => {
    return jogos.value.map(g => {
      const palpite = palpitesMap.value[g.match_id] || null
      const hasPalpite = !!palpite
      const isAberto = !g.status || g.status === 'agendado' || g.status === 'aberto'
      const isFinalizado = g.status === 'encerrado'
      const isBloqueado = g.status === 'bloqueado' || g.status === 'em_andamento'
      const golsCasa = g.gols_casa != null ? Number(g.gols_casa) : null
      const golsFora = g.gols_fora != null ? Number(g.gols_fora) : null

      let pontosGanhos = 0, exato = false
      if (isFinalizado && palpite && golsCasa != null) {
        const { calcPontos } = requireApi()
        pontosGanhos = calcPontos(palpite.goalsA, palpite.goalsB, golsCasa, golsFora)
        exato = pontosGanhos === 3
      }

      let statusLabel, statusColor, statusBg
      if (isAberto && hasPalpite) {
        statusLabel = 'Salvo ✓'; statusColor = '#00DC82'; statusBg = 'rgba(0,220,130,0.14)'
      } else if (isAberto) {
        statusLabel = 'Aberto'; statusColor = '#60A5FA'; statusBg = 'rgba(96,165,250,0.12)'
      } else if (isBloqueado) {
        statusLabel = 'Em andamento'; statusColor = '#FB923C'; statusBg = 'rgba(251,146,60,0.12)'
      } else {
        statusLabel = 'Finalizado'; statusColor = '#94A3B8'; statusBg = 'rgba(148,163,184,0.10)'
      }

      return {
        id: g.id || g.match_id,
        match_id: g.match_id,
        teamA: g.casa, teamB: g.fora,
        flagA: flag(g.casa), flagB: flag(g.fora),
        date: formatDate(g.kickoff),
        time: formatTime(g.kickoff),
        status: isAberto ? 'aberto' : isBloqueado ? 'bloqueado' : 'finalizado',
        grupo: g.grupo || '',
        kickoff: g.kickoff,
        resultado: golsCasa != null ? { goalsA: golsCasa, goalsB: golsFora } : null,
        palpite, hasPalpite, isAberto, isFinalizado, isBloqueado,
        pontosGanhos, exato,
        statusLabel, statusColor, statusBg,
        palpiteText: palpite ? `${palpite.goalsA} × ${palpite.goalsB}` : null,
        resultadoText: golsCasa != null ? `${golsCasa} × ${golsFora}` : null,
        pontosText: !hasPalpite ? null : exato ? '+3 🎯' : pontosGanhos > 0 ? '+1' : '+0',
        pontosColor: !hasPalpite ? '#94A3B8' : exato ? '#00DC82' : pontosGanhos > 0 ? '#60A5FA' : '#F87171',
      }
    })
  })

  const jogosFiltrados = computed(() => {
    const list = jogosEnriquecidos.value
    switch (filtro.value) {
      case 'abertos': return list.filter(g => g.isAberto && !g.hasPalpite)
      case 'meus': return list.filter(g => g.hasPalpite)
      case 'finalizados': return list.filter(g => g.isFinalizado)
      default: return list
    }
  })

  const semPalpite = computed(() => jogosEnriquecidos.value.filter(g => g.isAberto && !g.hasPalpite))
  const proximoJogo = computed(() => semPalpite.value[0] || null)
  const semPalpiteCount = computed(() => semPalpite.value.length)

  function setFiltro(val) { filtro.value = val }

  async function salvarPalpite(matchId, goalsA, goalsB) {
    if (!telegramId.value) return
    try {
      await apiSave(matchId, telegramId.value, user.value?.nome || '?', goalsA, goalsB)
      palpitesMap.value = { ...palpitesMap.value, [matchId]: { goalsA, goalsB } }
    } catch (e) {
      console.error('Failed to save palpite:', e)
      // Still save locally for UI responsiveness
      palpitesMap.value = { ...palpitesMap.value, [matchId]: { goalsA, goalsB } }
    }
  }

  function getJogo(id) {
    return jogosEnriquecidos.value.find(g => g.id === Number(id) || g.match_id === String(id)) || null
  }

  return {
    jogos: jogosEnriquecidos, jogosFiltrados, filtro, setFiltro,
    salvarPalpite, getJogo, proximoJogo, semPalpiteCount, loaded,
  }
}

// ─── helpers ────────────────────────────────────────────

let _api = null
function requireApi() {
  if (!_api) {
    // Will be populated when api module is loaded
    try {
      _api = { calcPontos: (a, b, c, d) => {
        if (a === c && b === d) return 3
        const s = (x, y) => (x > y ? 1 : x < y ? -1 : 0)
        return s(a, b) === s(c, d) ? 1 : 0
      }}
    } catch {}
  }
  return _api
}

const FLAGS = {
  'brasil': '🇧🇷', 'argentina': '🇦🇷', 'méxico': '🇲🇽', 'estados unidos': '🇺🇸', 'canadá': '🇨🇦',
  'alemanha': '🇩🇪', 'espanha': '🇪🇸', 'frança': '🇫🇷', 'inglaterra': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'portugal': '🇵🇹',
  'países baixos': '🇳🇱', 'bélgica': '🇧🇪', 'itália': '🇮🇹', 'croácia': '🇭🇷',
  'uruguai': '🇺🇾', 'colômbia': '🇨🇴', 'equador': '🇪🇨', 'paraguai': '🇵🇾', 'chile': '🇨🇱',
  'marrocos': '🇲🇦', 'senegal': '🇸🇳', 'argélia': '🇩🇿', 'tunísia': '🇹🇳', 'egito': '🇪🇬',
  'costa do marfim': '🇨🇮', 'gana': '🇬🇭', 'cabo verde': '🇨🇻', 'áfrica do sul': '🇿🇦',
  'japão': '🇯🇵', 'coreia do sul': '🇰🇷', 'arábia saudita': '🇸🇦', 'austrália': '🇦🇺', 'irã': '🇮🇷',
  'nova zelândia': '🇳🇿', 'catar': '🇶🇦', 'uzbequistão': '🇺🇿', 'iraque': '🇮🇶', 'jordânia': '🇯🇴',
  'suécia': '🇸🇪', 'noruega': '🇳🇴', 'suíça': '🇨🇭', 'áustria': '🇦🇹', 'turquia': '🇹🇷',
  'república tcheca': '🇨🇿', 'escócia': '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'bósnia e herzegovina': '🇧🇦',
  'curaçao': '🇨🇼', 'haiti': '🇭🇹', 'panamá': '🇵🇦',
  'república democrática do congo': '🇨🇩',
}
function flag(team) {
  if (!team) return '🏳️'
  const key = team.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  return FLAGS[key] || '🏳️'
}

function formatDate(iso) {
  if (!iso) return ''
  try {
    const [date] = iso.split('T')
    const [y, m, d] = date.split('-')
    return `${d}/${m}`
  } catch { return '' }
}
function formatTime(iso) {
  if (!iso) return ''
  try {
    const [, time] = iso.split('T')
    return time.slice(0, 5)
  } catch { return '' }
}
