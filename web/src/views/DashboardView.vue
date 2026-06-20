<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchJogos, fetchAllPalpites, fetchParticipantes, calcRanking } from '../api.js'

const router = useRouter()

// Public data — loaded on mount, no auth required
const jogos = ref([])
const rankingData = ref([])
const allPalpites = ref([])  // raw palpites for cross-table

onMounted(async () => {
  try {
    const [rawJogos, palpites, participantes] = await Promise.all([
      fetchJogos(), fetchAllPalpites(), fetchParticipantes(),
    ])
    allPalpites.value = palpites
    jogos.value = rawJogos.map(g => ({
      ...g,
      id: g.id || g.match_id,
      match_id: g.match_id,
      teamA: g.casa, teamB: g.fora,
      flagA: flag(g.casa), flagB: flag(g.fora),
      date: formatDate(g.kickoff),
      time: formatTime(g.kickoff),
      grupo: g.grupo || '',
      isFinalizado: g.status === 'encerrado',
      isAberto: !g.status || g.status === 'agendado' || g.status === 'aberto',
      isBloqueado: g.status === 'bloqueado' || g.status === 'em_andamento',
      resultado: g.gols_casa != null ? { goalsA: Number(g.gols_casa), goalsB: Number(g.gols_fora) } : null,
    }))
    rankingData.value = calcRanking(rawJogos, palpites, participantes)
  } catch (e) {
    console.warn('Dashboard fetch failed:', e.message)
  }
})

// Real palpites indexed by match_id -> telegram_id -> {a, b}
const palpitesMap = computed(() => {
  const map = {}
  for (const p of allPalpites.value) {
    if (!map[p.match_id]) map[p.match_id] = {}
    map[p.match_id][Number(p.telegram_id)] = { a: Number(p.gols_casa), b: Number(p.gols_fora), nome: p.nome }
  }
  return map
})

const rankingList = computed(() =>
  rankingData.value.map((r, i) => ({
    ...r,
    id: r.telegram_id || i,
    name: r.nome,
    posicao: i + 1,
    medal: i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : '',
    avatarColor: ['#F7C948','#94A3B8','#CD7F32','#60A5FA','#A78BFA','#4ADE80','#F87171'][i % 7],
    initial: (r.nome || '?')[0],
  }))
)

const page = ref('landing')
const selectedPlayerId = ref(null)
const selectedCountry = ref(null)
const selectedGroup = ref(null)
const showBreadcrumb = computed(() => page.value !== 'landing')

const finalizadoCount = computed(() => jogos.value.filter(g => g.isFinalizado).length)
const totalGames = computed(() => jogos.value.length)
const abertoCount = computed(() => jogos.value.filter(g => g.isAberto).length)
const totalPlayers = computed(() => rankingList.value.length)

const leader = computed(() => rankingList.value[0] || null)

const COLORS = ['#F7C948', '#94A3B8', '#CD7F32', '#60A5FA', '#A78BFA', '#4ADE80', '#F87171']
const PLAYER_NAMES = ['Ricardo', 'Pajé', 'Big', 'Flávia', 'Mari Gallo', 'Mari Som', 'Lere']

// ── Mock: all participants' guesses for each game ──
// Format: [playerIdx][gameId] = { a, b } or null
function buildAllGuesses() {
  const map = {}
  const games = jogos.value
  for (let pi = 0; pi < 7; pi++) {
    map[pi] = {}
    for (const g of games) {
      if (g.isFinalizado) {
        // For finalized games, determine based on quemCravou/quemVencedor
        const name = PLAYER_NAMES[pi]
        if ((g.quemCravou || []).includes(name)) {
          map[pi][g.id] = g.resultado ? { a: g.resultado.goalsA, b: g.resultado.goalsB } : null
        } else if ((g.quemVencedor || []).includes(name)) {
          const r = g.resultado
          if (r) {
            // Give a non-exact result that still gets winner right
            const shift = r.goalsA === r.goalsB ? 1 : 0
            map[pi][g.id] = { a: r.goalsA + (shift && pi % 2 ? 1 : 0), b: r.goalsB + (shift && pi % 2 === 0 ? 1 : 0) }
          }
        } else {
          map[pi][g.id] = { a: Math.floor(Math.random() * 4), b: Math.floor(Math.random() * 4) }
        }
      } else if (g.isBloqueado) {
        map[pi][g.id] = { a: Math.floor(Math.random() * 3), b: Math.floor(Math.random() * 3) }
      } else {
        // Aberto — random guesses
        map[pi][g.id] = Math.random() > 0.15 ? { a: Math.floor(Math.random() * 3), b: Math.floor(Math.random() * 3) } : null
      }
    }
  }
  return map
}

// ── Cross-table ──
function scoreType(palpite, resultado) {
  if (!palpite || !resultado) return { tipo: 'sem', pts: 0 }
  const { goalsA: rA, goalsB: rB } = resultado
  if (palpite.a === rA && palpite.b === rB) return { tipo: 'exato', pts: 3 }
  const rW = rA > rB ? 'A' : rB > rA ? 'B' : 'E'
  const pW = palpite.a > palpite.b ? 'A' : palpite.b > palpite.a ? 'B' : 'E'
  return rW === pW ? { tipo: 'vencedor', pts: 1 } : { tipo: 'errou', pts: 0 }
}
function cellStyle(scored) {
  const M = {
    exato:    ['rgba(0,220,130,0.15)',   '#00DC82', 'rgba(0,220,130,0.3)'],
    vencedor: ['rgba(96,165,250,0.12)',  '#60A5FA', 'rgba(96,165,250,0.22)'],
    errou:    ['rgba(248,113,113,0.1)',  '#F87171', 'rgba(248,113,113,0.22)'],
    bloqueado:['rgba(251,146,60,0.1)',   '#FB923C', 'rgba(251,146,60,0.22)'],
    aberto:   ['rgba(255,255,255,0.04)', '#7A8FA0', 'rgba(255,255,255,0.1)'],
    sem:      ['transparent',            '#2A3D52', 'rgba(255,255,255,0.05)'],
  }
  const [bg, color, bc] = M[scored.tipo] || M.sem
  return { bg, color, border: '1px solid ' + bc }
}

const allGuesses = ref(null)
const crossTableReady = ref(false)

// Build guesses on first load
import { watch } from 'vue'
watch(() => jogos.value.length, () => {
  if (jogos.value.length > 0 && !crossTableReady.value) {
    allGuesses.value = buildAllGuesses()
    crossTableReady.value = true
  }
}, { immediate: true })

const tableHeaderPlayers = computed(() =>
  rankingList.value.slice(0, 7).map((p, i) => ({
    ...p,
    initial: p.name[0],
    avatarBg: COLORS[i % COLORS.length],
    ptColor: i === 0 ? '#F7C948' : i === 1 ? '#94A3B8' : i === 2 ? '#CD7F32' : p.pontos >= 9 ? '#60A5FA' : '#7A8FA0',
    onClick: () => goToPlayer(p),
  }))
)

const activeTableRows = computed(() => {
  if (!crossTableReady.value || !allGuesses.value) return []
  return jogos.value.map(g => {
    const cells = PLAYER_NAMES.map((name, pi) => {
      const pal = (allGuesses.value[pi] || {})[g.id] || null
      const scored = g.isFinalizado && g.resultado
        ? scoreType(pal, g.resultado)
        : { tipo: g.isBloqueado ? 'bloqueado' : pal ? 'aberto' : 'sem', pts: 0 }
      const s = cellStyle(scored)
      return { ...s, label: pal ? (pal.a + '-' + pal.b) : '—' }
    })
    const statusBorderColor = g.isFinalizado ? '#1E3A5F' : g.isBloqueado ? 'var(--accent-orange)' : 'var(--accent-green)'
    return {
      ...g,
      cells,
      rowBg: g.isFinalizado ? '#0A1628' : g.isBloqueado ? 'rgba(251,146,60,0.025)' : 'rgba(0,220,130,0.015)',
      borderLeft: '3px solid ' + statusBorderColor,
      resultText: g.resultado ? (g.resultado.goalsA + '-' + g.resultado.goalsB) : g.isBloqueado ? '⏱' : '—',
      resultColor: g.isFinalizado ? '#EBF0F5' : g.isBloqueado ? 'var(--accent-orange)' : '#2A3D52',
    }
  })
})

// Generate mock guesses for each game (for two-column layout)
function generateGuesses(game) {
  if (game.isFinalizado) {
    const all = [...(game.quemCravou || []), ...(game.quemVencedor || [])]
    if (all.length === 0) {
      return PLAYER_NAMES.map((n, i) => ({
        name: n, initial: n[0], avatarBg: COLORS[i % COLORS.length],
        label: (Math.floor(Math.random() * 4)) + '-' + (Math.floor(Math.random() * 4)),
        labelColor: '#2A3D52',
      }))
    }
    return all.map((n, i) => {
      const pIdx = PLAYER_NAMES.indexOf(n)
      return { name: n, initial: n[0], avatarBg: COLORS[pIdx >= 0 ? pIdx % COLORS.length : i % COLORS.length], label: '✓', labelColor: '#EBF0F5' }
    })
  }
  return PLAYER_NAMES.map((n, i) => ({
    name: n, initial: n[0], avatarBg: COLORS[i % COLORS.length],
    label: (Math.floor(Math.random() * 3)) + '-' + (Math.floor(Math.random() * 3)),
    labelColor: '#EBF0F5',
  }))
}

// ── Player Detail ──
const selPlayer = computed(() => {
  if (!selectedPlayerId.value) return null
  return rankingList.value.find(p => p.id === selectedPlayerId.value) || null
})
const selPlayerPos = computed(() => selPlayer.value ? rankingList.value.findIndex(p => p.id === selPlayer.value.id) + 1 : 0)

const playerGameRows = computed(() => {
  if (!selPlayer.value || !allGuesses.value) return []
  const pIdx = PLAYER_NAMES.indexOf(selPlayer.value.name)
  if (pIdx < 0) return []
  let exatos = 0, vencedores = 0, erros = 0
  const rows = jogos.value.map(g => {
    const pal = (allGuesses.value[pIdx] || {})[g.id] || null
    const resultText = g.resultado ? (g.resultado.goalsA + '-' + g.resultado.goalsB) : ''
    const isFinalizado = g.isFinalizado
    const statusDot = g.isAberto ? (pal ? 'var(--accent-green)' : '#2A3D52')
      : g.isBloqueado ? 'var(--accent-orange)'
      : isFinalizado && pal
        ? (g.resultado && pal.a === g.resultado.goalsA && pal.b === g.resultado.goalsB ? 'var(--accent-green)'
          : (() => { const rv = g.resultado.goalsA > g.resultado.goalsB ? 'A' : g.resultado.goalsB > g.resultado.goalsA ? 'B' : 'E'
            const pv = pal.a > pal.b ? 'A' : pal.b > pal.a ? 'B' : 'E'
            return rv === pv ? 'var(--accent-blue)' : 'var(--accent-red)' })())
        : '#2A3D52'
    if (isFinalizado && pal && g.resultado) {
      const rv = g.resultado.goalsA > g.resultado.goalsB ? 'A' : g.resultado.goalsB > g.resultado.goalsA ? 'B' : 'E'
      const pv = pal.a > pal.b ? 'A' : pal.b > pal.a ? 'B' : 'E'
      const isExato = pal.a === g.resultado.goalsA && pal.b === g.resultado.goalsB
      if (isExato) exatos++
      else if (rv === pv) vencedores++
      else erros++
    }
    return { ...g, isFinalizado, pal, resultText, statusDot }
  })
  // Store computed stats for renderVals
  return { rows, exatos, vencedores, erros }
})

const selPlayerExatos = computed(() => playerGameRows.value?.exatos || 0)
const selPlayerVencedor = computed(() => playerGameRows.value?.vencedores || 0)
const selPlayerErrou = computed(() => playerGameRows.value?.erros || 0)

// ── Country Detail ──
const countryGames = computed(() =>
  selectedCountry.value ? jogos.value.filter(g => g.teamA === selectedCountry.value || g.teamB === selectedCountry.value) : []
)
const countryW = computed(() => countryGames.value.filter(g => g.isFinalizado && g.resultado && (
  (g.teamA === selectedCountry.value && g.resultado.goalsA > g.resultado.goalsB) ||
  (g.teamB === selectedCountry.value && g.resultado.goalsB > g.resultado.goalsA)
)).length)
const countryD = computed(() => countryGames.value.filter(g => g.isFinalizado && g.resultado && g.resultado.goalsA === g.resultado.goalsB).length)
const countryL = computed(() => countryGames.value.filter(g => g.isFinalizado && g.resultado && (
  (g.teamA === selectedCountry.value && g.resultado.goalsA < g.resultado.goalsB) ||
  (g.teamB === selectedCountry.value && g.resultado.goalsB < g.resultado.goalsA)
)).length)
const countryFlag = computed(() => {
  const cg = countryGames.value[0]
  if (!cg) return '🏳️'
  return cg.teamA === selectedCountry.value ? cg.flagA : cg.flagB
})
const countryGroupVal = computed(() => countryGames.value[0]?.grupo || '')

// ── Group Detail ──
const groupGames = computed(() =>
  selectedGroup.value ? jogos.value.filter(g => g.grupo === selectedGroup.value) : []
)
const groupStandings = computed(() => {
  const tsMap = {}
  for (const g of groupGames.value) {
    if (!tsMap[g.teamA]) tsMap[g.teamA] = { team: g.teamA, flag: g.flagA, w: 0, d: 0, l: 0, pts: 0, gf: 0, ga: 0 }
    if (!tsMap[g.teamB]) tsMap[g.teamB] = { team: g.teamB, flag: g.flagB, w: 0, d: 0, l: 0, pts: 0, gf: 0, ga: 0 }
  }
  for (const g of groupGames.value) {
    if (!g.isFinalizado || !g.resultado) continue
    const { goalsA: rA, goalsB: rB } = g.resultado
    tsMap[g.teamA].gf += rA; tsMap[g.teamA].ga += rB
    tsMap[g.teamB].gf += rB; tsMap[g.teamB].ga += rA
    if (rA > rB) { tsMap[g.teamA].w++; tsMap[g.teamA].pts += 3; tsMap[g.teamB].l++ }
    else if (rA === rB) { tsMap[g.teamA].d++; tsMap[g.teamA].pts++; tsMap[g.teamB].d++; tsMap[g.teamB].pts++ }
    else { tsMap[g.teamB].w++; tsMap[g.teamB].pts += 3; tsMap[g.teamA].l++ }
  }
  return Object.values(tsMap)
    .sort((a, b) => b.pts - a.pts || (b.gf - b.ga) - (a.gf - a.ga))
    .map((t, i) => ({ ...t, wdl: t.w + '-' + t.d + '-' + t.l, gfga: t.gf + ':' + t.ga, posColor: i === 0 ? 'var(--accent-green)' : i === 1 ? 'var(--accent-blue)' : 'var(--text-secondary)' }))
})

const proximosJogos = computed(() =>
  jogos.value.filter(g => !g.isFinalizado).map(g => ({
    ...g,
    statusBadge: g.isBloqueado ? '● Em andamento' : '● Aberto',
    statusColor: g.isBloqueado ? 'var(--accent-orange)' : 'var(--accent-green)',
    statusBg: g.isBloqueado ? 'rgba(251,146,60,0.12)' : 'rgba(0,220,130,0.1)',
    guesses: realGuesses(g),
  }))
)

// ── Helpers ──
const FLAGS = {
  // Portuguese
  'brasil': '🇧🇷', 'argentina': '🇦🇷', 'mexico': '🇲🇽', 'estados unidos': '🇺🇸', 'canada': '🇨🇦',
  'alemanha': '🇩🇪', 'espanha': '🇪🇸', 'franca': '🇫🇷', 'inglaterra': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'portugal': '🇵🇹',
  'paises baixos': '🇳🇱', 'belgica': '🇧🇪', 'italia': '🇮🇹', 'croacia': '🇭🇷',
  'uruguai': '🇺🇾', 'colombia': '🇨🇴', 'equador': '🇪🇨', 'paraguai': '🇵🇾', 'chile': '🇨🇱',
  'marrocos': '🇲🇦', 'senegal': '🇸🇳', 'argelia': '🇩🇿', 'tunisia': '🇹🇳', 'egito': '🇪🇬',
  'costa do marfim': '🇨🇮', 'gana': '🇬🇭', 'cabo verde': '🇨🇻', 'africa do sul': '🇿🇦',
  'japao': '🇯🇵', 'coreia do sul': '🇰🇷', 'arabia saudita': '🇸🇦', 'australia': '🇦🇺', 'ira': '🇮🇷',
  'nova zelandia': '🇳🇿', 'catar': '🇶🇦', 'uzbequistao': '🇺🇿', 'iraque': '🇮🇶', 'jordania': '🇯🇴',
  'suecia': '🇸🇪', 'noruega': '🇳🇴', 'suica': '🇨🇭', 'austria': '🇦🇹', 'turquia': '🇹🇷',
  'republica tcheca': '🇨🇿', 'escocia': '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'bosnia e herzegovina': '🇧🇦',
  'curacao': '🇨🇼', 'haiti': '🇭🇹', 'panama': '🇵🇦', 'republica democratica do congo': '🇨🇩',
  // English
  'brazil': '🇧🇷', 'mexico': '🇲🇽', 'united states': '🇺🇸', 'usa': '🇺🇸',
  'germany': '🇩🇪', 'spain': '🇪🇸', 'france': '🇫🇷', 'england': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  'netherlands': '🇳🇱', 'belgium': '🇧🇪', 'italy': '🇮🇹', 'croatia': '🇭🇷',
  'uruguay': '🇺🇾', 'ecuador': '🇪🇨', 'paraguay': '🇵🇾',
  'morocco': '🇲🇦', 'algeria': '🇩🇿', 'tunisia': '🇹🇳', 'egypt': '🇪🇬',
  'ivory coast': '🇨🇮', 'ghana': '🇬🇭', 'cape verde': '🇨🇻', 'south africa': '🇿🇦',
  'japan': '🇯🇵', 'south korea': '🇰🇷', 'saudi arabia': '🇸🇦', 'iran': '🇮🇷',
  'new zealand': '🇳🇿', 'qatar': '🇶🇦', 'uzbekistan': '🇺🇿', 'iraq': '🇮🇶', 'jordan': '🇯🇴',
  'sweden': '🇸🇪', 'norway': '🇳🇴', 'switzerland': '🇨🇭', 'austria': '🇦🇹', 'turkey': '🇹🇷',
  'czech republic': '🇨🇿', 'scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'bosnia and herzegovina': '🇧🇦',
  'curacao': '🇨🇼', 'panama': '🇵🇦', 'democratic republic of congo': '🇨🇩',
  'dr congo': '🇨🇩', 'colombia': '🇨🇴', 'chile': '🇨🇱', 'senegal': '🇸🇳',
  'portugal': '🇵🇹', 'canada': '🇨🇦', 'argentina': '🇦🇷', 'haiti': '🇭🇹',
}
function flag(team) {
  if (!team) return '🏳️'
  const key = team.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
  return FLAGS[key] || '🏳️'
}
function formatDate(iso) {
  if (!iso) return ''
  try { const [y, m, d] = iso.split('T')[0].split('-'); return `${d}/${m}` } catch { return '' }
}
function formatTime(iso) {
  if (!iso) return ''
  try { return iso.split('T')[1]?.slice(0, 5) || '' } catch { return '' }
}

function realGuesses(game) {
  const gameMap = palpitesMap.value[game.match_id] || {}
  return rankingList.value.map((r, i) => {
    const pal = gameMap[Number(r.id)]
    return {
      name: r.name,
      initial: r.initial,
      avatarBg: r.avatarColor,
      label: pal ? `${pal.a}-${pal.b}` : '—',
      labelColor: pal ? '#EBF0F5' : '#2A3D52',
    }
  })
}

function goHome() {
  page.value = 'landing'
}

function goBack() {
  page.value = 'landing'
  selectedPlayerId.value = null
  selectedCountry.value = null
  selectedGroup.value = null
}

function goToPlayer(player) {
  selectedPlayerId.value = player.id
  selectedCountry.value = null
  selectedGroup.value = null
  page.value = 'player'
}

function goToCountry(teamName) {
  selectedCountry.value = teamName
  selectedPlayerId.value = null
  selectedGroup.value = null
  page.value = 'country'
}

function goToGroup(grupo) {
  selectedGroup.value = grupo
  selectedPlayerId.value = null
  selectedCountry.value = null
  page.value = 'group'
}
</script>

<template>
  <div class="dashboard">
    <!-- STICKY HEADER -->
    <header class="dash-header">
      <div class="dash-header-inner">
        <div class="dash-brand" @click="goHome">
          <span class="dash-logo">⚽</span>
          <span class="dash-name">Big Bolão</span>
          <span class="dash-badge">COPA 2026</span>
        </div>
        <div class="dash-header-spacer" />
        <button v-if="showBreadcrumb" class="dash-back-btn" @click="goBack">
          ← Voltar
        </button>
        <div class="dash-progress">
          <span class="dash-progress-dot" />
          <span class="dash-progress-text">
            <span class="dash-progress-count">{{ finalizadoCount }}</span>
            <span class="dash-progress-sep">/</span>
            <span class="dash-progress-total">{{ totalGames }}</span>
            <span class="dash-progress-label"> jogos finalizados</span>
          </span>
        </div>
      </div>
    </header>

    <!-- MAIN CONTENT -->
    <main class="dash-main">
      <!-- PLAYER DETAIL -->
      <div v-if="page === 'player' && selPlayer" class="dash-player-page">
        <div class="dash-player-header">
          <div class="dash-player-avatar-big" :style="{ background: selPlayer.avatarColor }">{{ selPlayer.initial }}</div>
          <div>
            <h1 class="dash-player-name">{{ selPlayer.name }}</h1>
            <p class="dash-player-pos">#{{ selPlayerPos }} no ranking</p>
          </div>
        </div>
        <div class="dash-player-stats-grid">
          <div class="dash-player-stat">
            <p class="dash-player-stat-val gold">{{ selPlayer.pontos }}</p>
            <p class="dash-player-stat-label">Pontos</p>
          </div>
          <div class="dash-player-stat">
            <p class="dash-player-stat-val green">{{ selPlayerExatos }}</p>
            <p class="dash-player-stat-label">🎯 Exatos</p>
          </div>
          <div class="dash-player-stat">
            <p class="dash-player-stat-val blue">{{ selPlayerVencedor }}</p>
            <p class="dash-player-stat-label">✓ Vencedores</p>
          </div>
          <div class="dash-player-stat">
            <p class="dash-player-stat-val red">{{ selPlayerErrou }}</p>
            <p class="dash-player-stat-label">✗ Erros</p>
          </div>
        </div>
        <p class="dash-col-label" style="margin-bottom: 14px;">PALPITES DE {{ selPlayer.name?.toUpperCase() }}</p>
        <div class="dash-player-games-list">
          <div v-for="g in playerGameRows?.rows" :key="g.id" class="dash-pg-row">
            <span class="dash-pg-dot" :style="{ background: g.statusDot }"></span>
            <div class="dash-pg-teams">
              <span class="dash-pg-flag">{{ g.flagA }}</span>
              <span class="dash-pg-team">{{ g.teamA }}</span>
              <span class="dash-pg-vs">×</span>
              <span class="dash-pg-team">{{ g.teamB }}</span>
              <span class="dash-pg-flag">{{ g.flagB }}</span>
            </div>
            <div class="dash-pg-meta">
              <span class="dash-pg-meta-line">{{ g.date }} · {{ g.time }}</span>
              <span class="dash-pg-meta-line">{{ g.grupo }}</span>
            </div>
            <div v-if="g.isFinalizado" class="dash-pg-resultado">
              <p class="dash-pg-rlabel">Resultado</p>
              <p class="dash-pg-rscore">{{ g.resultText }}</p>
            </div>
            <div class="dash-pg-palpite">
              <p class="dash-pg-rlabel">Palpite</p>
              <div class="dash-pg-pchip" :style="{
                background: g.pal ? 'rgba(255,255,255,0.08)' : 'transparent',
                color: g.pal ? 'var(--text-primary)' : '#2A3D52',
                border: g.pal ? '1px solid rgba(255,255,255,0.12)' : '1px solid rgba(255,255,255,0.04)'
              }">{{ g.pal ? (g.pal.a + '-' + g.pal.b) : '—' }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- COUNTRY DETAIL -->
      <div v-if="page === 'country' && selectedCountry" class="dash-country-page">
        <div class="dash-country-header">
          <span class="dash-country-flag-big">{{ countryFlag }}</span>
          <div>
            <h1 class="dash-country-name">{{ selectedCountry }}</h1>
            <span class="dash-country-group-btn" @click="goToGroup(countryGroupVal)">{{ countryGroupVal }} →</span>
          </div>
          <div class="dash-country-stats">
            <div class="dash-cstat">
              <p class="dash-cstat-val green">{{ countryW }}</p>
              <p class="dash-cstat-label">Vitórias</p>
            </div>
            <div class="dash-cstat">
              <p class="dash-cstat-val gold">{{ countryD }}</p>
              <p class="dash-cstat-label">Empates</p>
            </div>
            <div class="dash-cstat">
              <p class="dash-cstat-val red">{{ countryL }}</p>
              <p class="dash-cstat-label">Derrotas</p>
            </div>
          </div>
        </div>
      </div>

      <!-- GROUP DETAIL -->
      <div v-if="page === 'group' && selectedGroup" class="dash-group-page">
        <div class="dash-group-header">
          <h1 class="dash-group-title">{{ selectedGroup }}</h1>
          <p class="dash-group-subtitle">Classificação e palpites</p>
        </div>
        <p class="dash-col-label">CLASSIFICAÇÃO</p>
        <div class="dash-group-standings">
          <div class="dash-gs-header">
            <div></div>
            <div class="dash-gs-hcell">Seleção</div>
            <div class="dash-gs-hcell center">Pts</div>
            <div class="dash-gs-hcell center">V–E–D</div>
            <div class="dash-gs-hcell center">GP:GS</div>
          </div>
          <div v-for="s in groupStandings" :key="s.team" class="dash-gs-row" @click="goToCountry(s.team)">
            <div class="dash-gs-pos"><span class="dash-gs-pos-dot" :style="{ background: s.posColor }"></span></div>
            <div class="dash-gs-team">
              <span class="dash-gs-flag">{{ s.flag }}</span>
              <span class="dash-gs-team-name">{{ s.team }}</span>
            </div>
            <div class="dash-gs-cell"><span class="dash-gs-pts" :style="{ color: s.posColor }">{{ s.pts }}</span></div>
            <div class="dash-gs-cell"><span class="dash-gs-wdl">{{ s.wdl }}</span></div>
            <div class="dash-gs-cell"><span class="dash-gs-gfga">{{ s.gfga }}</span></div>
          </div>
        </div>
      </div>

      <!-- LANDING -->
      <div v-if="page === 'landing'" class="dash-landing">
        <!-- Hero -->
        <div class="dash-hero">
          <div>
            <h1 class="dash-hero-title">Bolão da Copa 2026</h1>
            <p class="dash-hero-subtitle">
              {{ totalPlayers }} participantes · {{ finalizadoCount }} jogos finalizados · {{ abertoCount }} abertos para palpitar
            </p>
          </div>
          <div v-if="leader" class="dash-leader-card" @click="goToPlayer(leader)">
            <span class="dash-leader-icon">🏆</span>
            <div>
              <p class="dash-leader-label">Líder atual</p>
              <p class="dash-leader-name">{{ leader.name }} · {{ leader.pontos }} pts</p>
            </div>
          </div>
        </div>

        <!-- Two-column layout -->
        <div class="dash-two-col">
          <!-- LEFT: Proximos jogos -->
          <div class="dash-col-left">
            <p class="dash-col-label">PRÓXIMOS JOGOS &amp; EM ANDAMENTO</p>
            <div class="dash-games-list">
              <div v-for="jogo in proximosJogos" :key="jogo.id" class="dash-game-card">
                <!-- Header row -->
                <div class="dash-game-header">
                  <span class="dash-game-badge" :style="{ color: jogo.statusColor, background: jogo.statusBg }">
                    {{ jogo.statusBadge }}
                  </span>
                  <span class="dash-game-grupo-btn" @click="goToGroup(jogo.grupo)">{{ jogo.grupo }}</span>
                  <span class="dash-game-date">{{ jogo.date }} · {{ jogo.time }}</span>
                </div>
                <!-- Teams -->
                <div class="dash-game-teams">
                  <div class="dash-game-team" @click="goToCountry(jogo.teamA)">
                    <span class="dash-game-flag">{{ jogo.flagA }}</span>
                    <span class="dash-game-team-name">{{ jogo.teamA }}</span>
                  </div>
                  <span class="dash-game-vs">×</span>
                  <div class="dash-game-team right" @click="goToCountry(jogo.teamB)">
                    <span class="dash-game-team-name">{{ jogo.teamB }}</span>
                    <span class="dash-game-flag">{{ jogo.flagB }}</span>
                  </div>
                </div>
                <!-- Guesses -->
                <div class="dash-game-guesses">
                  <span class="dash-guesses-label">Palpites</span>
                  <div v-for="g in jogo.guesses" :key="g.name" class="dash-guess-chip">
                    <div class="dash-guess-avatar" :style="{ background: g.avatarBg }">{{ g.initial }}</div>
                    <span class="dash-guess-score" :style="{ color: g.labelColor }">{{ g.label }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- RIGHT: Ranking sidebar -->
          <div class="dash-col-right">
            <p class="dash-col-label">🏆 RANKING</p>
            <div class="dash-ranking-box">
              <div
                v-for="(r, i) in rankingList"
                :key="r.id"
                class="dash-rank-row"
                @click="goToPlayer(r)"
              >
                <span class="dash-rank-pos">{{ r.posicao }}</span>
                <span class="dash-rank-medal">{{ r.medal }}</span>
                <div class="dash-rank-avatar" :style="{ background: r.avatarColor }">{{ r.initial }}</div>
                <div class="dash-rank-info">
                  <p class="dash-rank-name">{{ r.name }}</p>
                  <p class="dash-rank-exatos">{{ r.exatos }} exato(s)</p>
                </div>
                <div class="dash-rank-pts-block">
                  <p class="dash-rank-pts" :style="{ color: i < 3 ? ['#F7C948','#94A3B8','#CD7F32'][i] : 'var(--text-primary)' }">
                    {{ r.pontos }}
                  </p>
                  <p class="dash-rank-pts-label">pts</p>
                </div>
              </div>
            </div>

            <!-- Como pontuar -->
            <div class="dash-scoring-card">
              <p class="dash-scoring-title">Como pontuar</p>
              <div class="dash-scoring-rows">
                <div class="dash-scoring-row">
                  <span class="dash-scoring-icon">🎯</span>
                  <span class="dash-scoring-text"><strong class="green">+3</strong> placar exato</span>
                </div>
                <div class="dash-scoring-row">
                  <span class="dash-scoring-icon">✓</span>
                  <span class="dash-scoring-text"><strong class="blue">+1</strong> vencedor / empate</span>
                </div>
                <div class="dash-scoring-row">
                  <span class="dash-scoring-icon">✗</span>
                  <span class="dash-scoring-text"><strong class="red">0</strong> erro</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Cross-table header + legend -->
        <div class="dash-table-section">
          <div class="dash-table-header-row">
            <p class="dash-col-label">TODOS OS PALPITES</p>
            <div class="dash-legend">
              <div class="dash-legend-item"><span class="dash-legend-dot" style="background:rgba(0,220,130,0.35)"></span> Exato +3</div>
              <div class="dash-legend-item"><span class="dash-legend-dot" style="background:rgba(96,165,250,0.35)"></span> Vencedor +1</div>
              <div class="dash-legend-item"><span class="dash-legend-dot" style="background:rgba(248,113,113,0.3)"></span> Errou</div>
              <div class="dash-legend-item"><span class="dash-legend-dot" style="background:rgba(251,146,60,0.3)"></span> Em andamento</div>
            </div>
          </div>

          <div class="dash-table-wrapper">
            <div class="dash-table-inner">
              <!-- Header row -->
              <div class="dash-tr dash-tr-header">
                <div class="dash-th dash-th-game">Jogo</div>
                <div class="dash-th dash-th-group">Grupo</div>
                <div class="dash-th dash-th-score">Placar</div>
                <div
                  v-for="ph in tableHeaderPlayers"
                  :key="ph.id"
                  class="dash-th dash-th-player"
                  @click="ph.onClick"
                >
                  <div class="dash-th-avatar" :style="{ background: ph.avatarBg }">{{ ph.initial }}</div>
                  <span class="dash-th-name">{{ ph.name }}</span>
                  <span class="dash-th-pts" :style="{ color: ph.ptColor }">{{ ph.pontos }}<span class="dash-th-pts-label"> pts</span></span>
                </div>
              </div>
              <!-- Data rows -->
              <div
                v-for="row in activeTableRows"
                :key="row.id"
                class="dash-tr dash-tr-data"
                :style="{ background: row.rowBg }"
              >
                <div class="dash-td dash-td-game" :style="{ borderLeft: row.borderLeft }">
                  <div class="dash-td-teams">
                    <span class="dash-td-flag" @click="goToCountry(row.teamA)">{{ row.flagA }}</span>
                    <span class="dash-td-team-name">{{ row.teamA }}</span>
                    <span class="dash-td-vs">×</span>
                    <span class="dash-td-team-name">{{ row.teamB }}</span>
                    <span class="dash-td-flag" @click="goToCountry(row.teamB)">{{ row.flagB }}</span>
                  </div>
                  <span class="dash-td-date">{{ row.date }} · {{ row.time }}</span>
                </div>
                <div class="dash-td dash-td-group">
                  <span class="dash-td-grupo-btn" @click="goToGroup(row.grupo)">{{ row.grupo }}</span>
                </div>
                <div class="dash-td dash-td-score">
                  <span class="dash-td-score-text" :style="{ color: row.resultColor }">{{ row.resultText }}</span>
                </div>
                <div
                  v-for="(cell, ci) in row.cells"
                  :key="ci"
                  class="dash-td dash-td-cell"
                >
                  <div
                    class="dash-cell-palpite"
                    :style="{ background: cell.bg, color: cell.color, border: cell.border }"
                  >{{ cell.label }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: var(--bg-deep);
  color: var(--text-primary);
  animation: fadeIn 0.2s ease;
}

/* ─── Sticky Header ─── */
.dash-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(3, 11, 22, 0.96);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-subtle);
}
.dash-header-inner {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 32px;
  height: 54px;
  display: flex;
  align-items: center;
  gap: 16px;
}
.dash-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  flex-shrink: 0;
}
.dash-logo {
  font-size: 22px;
  line-height: 1;
}
.dash-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}
.dash-badge {
  font-size: 11px;
  font-weight: 700;
  color: var(--accent-gold);
  letter-spacing: 1.2px;
  background: rgba(247, 201, 72, 0.12);
  padding: 2px 9px;
  border-radius: 20px;
}
.dash-header-spacer {
  flex: 1;
}
.dash-back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-tertiary);
  padding: 6px 14px;
  border-radius: 8px;
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
.dash-progress {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-shrink: 0;
}
.dash-progress-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent-green);
  display: inline-block;
}
.dash-progress-text {
  font-size: 13px;
  color: var(--text-muted);
}
.dash-progress-count {
  color: var(--text-tertiary);
  font-weight: 600;
}
.dash-progress-sep {
  color: var(--text-muted);
}
.dash-progress-total {
  color: var(--text-tertiary);
}
.dash-progress-label {
  color: var(--text-muted);
}

/* ─── Main Content ─── */
.dash-main {
  max-width: 1440px;
  margin: 0 auto;
  padding: 36px 32px;
}
.dash-landing {
  animation: fadeInUp 0.3s ease;
}

/* ─── Hero ─── */
.dash-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}
.dash-hero-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.7px;
}
.dash-hero-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 5px;
}
.dash-leader-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(247, 201, 72, 0.08);
  border: 1px solid rgba(247, 201, 72, 0.18);
  border-radius: 12px;
  padding: 10px 18px;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s;
}
.dash-leader-card:hover {
  background: rgba(247, 201, 72, 0.14);
}
.dash-leader-icon {
  font-size: 20px;
}
.dash-leader-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--accent-gold);
  text-transform: uppercase;
  letter-spacing: 1.2px;
  margin-bottom: 3px;
}
.dash-leader-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}

/* ─── Two-column layout ─── */
.dash-two-col {
  display: grid;
  grid-template-columns: 1fr 296px;
  gap: 28px;
  align-items: start;
}
.dash-col-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1.2px;
  margin-bottom: 14px;
}

/* ─── Games list ─── */
.dash-games-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.dash-game-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  overflow: hidden;
}
.dash-game-header {
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: #0A1628;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.dash-game-badge {
  font-size: 12px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 20px;
  flex-shrink: 0;
}
.dash-game-grupo-btn {
  font-size: 11px;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.07);
  padding: 3px 8px;
  border-radius: 5px;
  font-weight: 600;
  cursor: pointer;
}
.dash-game-date {
  margin-left: auto;
  font-size: 12px;
  color: var(--text-muted);
  flex-shrink: 0;
}
.dash-game-teams {
  padding: 14px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.dash-game-team {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}
.dash-game-team.right {
  justify-content: flex-end;
}
.dash-game-flag {
  font-size: 28px;
  line-height: 1;
  flex-shrink: 0;
}
.dash-game-team-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}
.dash-game-vs {
  font-size: 16px;
  font-weight: 700;
  color: #1E3A5F;
  flex-shrink: 0;
}
.dash-game-guesses {
  padding: 10px 14px;
  background: rgba(0, 0, 0, 0.22);
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.dash-guesses-label {
  font-size: 10px;
  font-weight: 700;
  color: #2A3D52;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-right: 6px;
  flex-shrink: 0;
}
.dash-guess-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 20px;
  padding: 3px 8px 3px 4px;
  flex-shrink: 0;
}
.dash-guess-avatar {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 700;
  color: #030B16;
  flex-shrink: 0;
}
.dash-guess-score {
  font-size: 12px;
  font-weight: 600;
  font-family: 'Fira Code', 'Courier New', monospace;
}

/* ─── Ranking sidebar ─── */
.dash-ranking-box {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  overflow: hidden;
  margin-bottom: 14px;
}
.dash-rank-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  cursor: pointer;
  transition: background 0.1s;
}
.dash-rank-row:hover {
  background: rgba(255, 255, 255, 0.03);
}
.dash-rank-row:last-child {
  border-bottom: none;
}
.dash-rank-pos {
  font-size: 12px;
  color: #2A3D52;
  font-weight: 700;
  width: 16px;
  text-align: right;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}
.dash-rank-medal {
  font-size: 14px;
  width: 18px;
  text-align: center;
  flex-shrink: 0;
  line-height: 1;
}
.dash-rank-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #030B16;
  flex-shrink: 0;
}
.dash-rank-info {
  flex: 1;
  min-width: 0;
}
.dash-rank-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.dash-rank-exatos {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 1px;
}
.dash-rank-pts-block {
  text-align: right;
  flex-shrink: 0;
}
.dash-rank-pts {
  font-size: 16px;
  font-weight: 700;
  line-height: 1;
}
.dash-rank-pts-label {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 1px;
}

/* ─── Como pontuar ─── */
.dash-scoring-card {
  background: rgba(96, 165, 250, 0.06);
  border: 1px solid rgba(96, 165, 250, 0.13);
  border-radius: 10px;
  padding: 12px 14px;
}
.dash-scoring-title {
  font-size: 10px;
  font-weight: 700;
  color: var(--accent-blue);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 8px;
}
.dash-scoring-rows {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.dash-scoring-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.dash-scoring-icon {
  font-size: 13px;
  flex-shrink: 0;
}
.dash-scoring-text {
  font-size: 12px;
  color: var(--text-secondary);
}
.dash-scoring-text .green { color: var(--accent-green); }
.dash-scoring-text .blue { color: var(--accent-blue); }
.dash-scoring-text .red { color: var(--accent-red); }

/* ─── Cross-table ─── */
.dash-table-section {
  margin-top: 36px;
}
.dash-table-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 14px;
}
.dash-table-header-row .dash-col-label {
  margin-bottom: 0;
}
.dash-legend {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.dash-legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}
.dash-legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  display: inline-block;
  flex-shrink: 0;
}

.dash-table-wrapper {
  overflow-x: auto;
  border-radius: 14px;
  border: 1px solid var(--border-subtle);
}
.dash-table-inner {
  min-width: 900px;
}
.dash-tr {
  display: grid;
  grid-template-columns: 210px 72px 72px repeat(7, minmax(78px, 1fr));
}
.dash-tr-header {
  background: #0A1628;
  border-bottom: 2px solid rgba(255, 255, 255, 0.08);
}
.dash-tr-data {
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}
.dash-tr-data:last-child {
  border-bottom: none;
}

.dash-th {
  padding: 12px 8px;
  font-size: 10px;
  font-weight: 700;
  color: #2A3D52;
  text-transform: uppercase;
  letter-spacing: 1.2px;
}
.dash-th-game {
  padding: 12px 14px;
}
.dash-th-player {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  border-left: 1px solid rgba(255, 255, 255, 0.05);
  padding: 10px 4px;
  transition: background 0.1s;
}
.dash-th-player:hover {
  background: rgba(255, 255, 255, 0.03);
}
.dash-th-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #030B16;
  flex-shrink: 0;
}
.dash-th-name {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-align: center;
  line-height: 1.2;
  max-width: 70px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dash-th-pts {
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
}
.dash-th-pts-label {
  font-size: 9px;
  color: #2A3D52;
  font-weight: 500;
}

.dash-td {
  padding: 12px 8px;
  display: flex;
  align-items: center;
}
.dash-td-game {
  padding: 12px 14px 12px 11px;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 5px;
}
.dash-td-teams {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.dash-td-flag {
  font-size: 17px;
  line-height: 1;
  cursor: pointer;
  flex-shrink: 0;
}
.dash-td-team-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
}
.dash-td-vs {
  font-size: 11px;
  color: #1E3A5F;
  font-weight: 700;
  flex-shrink: 0;
}
.dash-td-date {
  font-size: 10px;
  color: #2A3D52;
}
.dash-td-group {
  justify-content: center;
}
.dash-td-grupo-btn {
  font-size: 10px;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 4px 7px;
  border-radius: 6px;
  font-weight: 600;
  white-space: nowrap;
  line-height: 1.3;
  text-align: center;
  cursor: pointer;
}
.dash-td-score {
  justify-content: center;
}
.dash-td-score-text {
  font-size: 14px;
  font-weight: 700;
  font-family: 'Fira Code', 'Courier New', monospace;
  letter-spacing: 1px;
  white-space: nowrap;
}
.dash-td-cell {
  justify-content: center;
  border-left: 1px solid rgba(255, 255, 255, 0.04);
}
.dash-cell-palpite {
  font-size: 13px;
  font-weight: 700;
  font-family: 'Fira Code', 'Courier New', monospace;
  letter-spacing: 1px;
  line-height: 1.3;
  padding: 5px 7px;
  border-radius: 7px;
  min-width: 44px;
  text-align: center;
}

/* ─── Player Detail ─── */
.dash-player-page { animation: fadeInUp 0.3s ease; }
.dash-player-header {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 24px;
}
.dash-player-avatar-big {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  color: #030B16;
  flex-shrink: 0;
}
.dash-player-name { font-size: 24px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.5px; }
.dash-player-pos { font-size: 14px; color: var(--text-secondary); margin-top: 3px; }
.dash-player-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 28px;
}
.dash-player-stat {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}
.dash-player-stat-val { font-size: 32px; font-weight: 700; line-height: 1; letter-spacing: -1px; }
.dash-player-stat-val.gold { color: var(--accent-gold); }
.dash-player-stat-val.green { color: var(--accent-green); }
.dash-player-stat-val.blue { color: var(--accent-blue); }
.dash-player-stat-val.red { color: var(--accent-red); }
.dash-player-stat-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 6px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}
.dash-player-games-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.dash-pg-row {
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 14px 18px;
  flex-wrap: wrap;
}
.dash-pg-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dash-pg-teams {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 200px;
}
.dash-pg-flag { font-size: 20px; line-height: 1; flex-shrink: 0; }
.dash-pg-team { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.dash-pg-vs { color: #2A3D52; font-size: 12px; }
.dash-pg-meta { display: flex; flex-direction: column; gap: 2px; flex-shrink: 0; min-width: 88px; }
.dash-pg-meta-line { font-size: 11px; color: var(--text-muted); }
.dash-pg-resultado { text-align: center; min-width: 64px; flex-shrink: 0; }
.dash-pg-rlabel { font-size: 10px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 3px; }
.dash-pg-rscore { font-size: 18px; font-weight: 700; color: var(--text-primary); font-family: 'Fira Code', monospace; letter-spacing: 2px; line-height: 1; }
.dash-pg-palpite { text-align: center; min-width: 76px; flex-shrink: 0; }
.dash-pg-pchip {
  display: inline-block;
  border-radius: 8px;
  padding: 5px 12px;
  font-size: 15px;
  font-weight: 700;
  font-family: 'Fira Code', monospace;
  letter-spacing: 2px;
  min-width: 60px;
  text-align: center;
}

/* ─── Country Detail ─── */
.dash-country-page { animation: fadeInUp 0.3s ease; }
.dash-country-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}
.dash-country-flag-big { font-size: 52px; line-height: 1; flex-shrink: 0; }
.dash-country-name { font-size: 24px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.5px; }
.dash-country-group-btn {
  margin-top: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--accent-blue);
  background: rgba(96,165,250,0.1);
  border: 1px solid rgba(96,165,250,0.2);
  padding: 4px 12px;
  border-radius: 20px;
  display: inline-block;
  cursor: pointer;
}
.dash-country-stats {
  margin-left: auto;
  display: flex;
  gap: 12px;
  flex-shrink: 0;
  flex-wrap: wrap;
}
.dash-cstat {
  text-align: center;
  padding: 14px 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  min-width: 72px;
}
.dash-cstat-val { font-size: 26px; font-weight: 700; line-height: 1; }
.dash-cstat-val.green { color: var(--accent-green); }
.dash-cstat-val.gold { color: var(--accent-gold); }
.dash-cstat-val.red { color: var(--accent-red); }
.dash-cstat-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
  margin-top: 4px;
  font-weight: 700;
}

/* ─── Group Detail ─── */
.dash-group-page { animation: fadeInUp 0.3s ease; }
.dash-group-header { margin-bottom: 28px; }
.dash-group-title { font-size: 24px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.5px; }
.dash-group-subtitle { font-size: 14px; color: var(--text-secondary); margin-top: 4px; }
.dash-group-standings {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  overflow: hidden;
}
.dash-gs-header {
  display: grid;
  grid-template-columns: 28px 1fr 48px 72px 60px;
  padding: 10px 14px;
  background: #0A1628;
  border-bottom: 1px solid rgba(255,255,255,0.07);
}
.dash-gs-hcell {
  font-size: 10px;
  font-weight: 700;
  color: #2A3D52;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.dash-gs-hcell.center { text-align: center; }
.dash-gs-row {
  display: grid;
  grid-template-columns: 28px 1fr 48px 72px 60px;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  cursor: pointer;
  transition: background 0.1s;
}
.dash-gs-row:hover { background: rgba(255,255,255,0.03); }
.dash-gs-row:last-child { border-bottom: none; }
.dash-gs-pos { display: flex; align-items: center; }
.dash-gs-pos-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dash-gs-team { display: flex; align-items: center; gap: 8px; }
.dash-gs-flag { font-size: 20px; line-height: 1; flex-shrink: 0; }
.dash-gs-team-name { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.dash-gs-cell { display: flex; align-items: center; justify-content: center; }
.dash-gs-pts { font-size: 15px; font-weight: 700; }
.dash-gs-wdl { font-size: 13px; color: var(--text-secondary); font-family: 'Fira Code', monospace; }
.dash-gs-gfga { font-size: 13px; color: var(--text-secondary); font-family: 'Fira Code', monospace; }
</style>
