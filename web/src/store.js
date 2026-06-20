import { ref, computed } from 'vue'
import { fetchJogos, fetchAllPalpites, fetchParticipantes, calcRanking, findUser, flag, fmtDate, fmtTime, calcPontos } from './api.js'

export const jogos = ref([])
export const palpites = ref([])
export const participantes = ref([])
export const ranking = ref([])
export const loaded = ref(false)
export const user = ref(null)  // { telegram_id, nome, ... }

export const finalizados = computed(() => jogos.value.filter(j => j.status === 'encerrado').length)
export const total = computed(() => jogos.value.length)
export const abertos = computed(() => jogos.value.filter(j => !j.status || j.status === 'agendado' || j.status === 'aberto').length)

export async function loadAll() {
  if (loaded.value) return
  try {
    const [j, p, parts] = await Promise.all([fetchJogos(), fetchAllPalpites(), fetchParticipantes()])
    jogos.value = j
    palpites.value = p
    participantes.value = parts
    ranking.value = calcRanking(j, p, parts)
  } catch (e) {
    console.error('Load failed:', e.message)
  }
  loaded.value = true
}

export async function reloadPalpites() {
  try {
    const p = await fetchAllPalpites()
    palpites.value = p
    ranking.value = calcRanking(jogos.value, p, participantes.value)
  } catch (e) { console.error(e) }
}

export async function initUser(uid) {
  if (!uid) return
  try {
    const found = await findUser(uid)
    if (found) user.value = found
  } catch (e) { console.error(e) }
}

// Derived: jogos enriched with flags/formatting
export const jogosRich = computed(() =>
  jogos.value.map(g => ({
    ...g,
    flagA: flag(g.casa),
    flagB: flag(g.fora),
    date: fmtDate(g.kickoff),
    time: fmtTime(g.kickoff),
    isFinalizado: g.status === 'encerrado',
    isAberto: !g.status || g.status === 'agendado' || g.status === 'aberto',
    isBloqueado: g.status === 'bloqueado' || g.status === 'em_andamento',
    resultado: g.gols_casa != null ? `${g.gols_casa}–${g.gols_fora}` : null,
  }))
)

// Palpites indexed: match_id → telegram_id → { a, b, nome }
export const palpitesIdx = computed(() => {
  const idx = {}
  for (const p of palpites.value) {
    if (!idx[p.match_id]) idx[p.match_id] = {}
    idx[p.match_id][Number(p.telegram_id)] = {
      a: Number(p.gols_casa), b: Number(p.gols_fora), nome: p.nome,
    }
  }
  return idx
})

// Active (ativo) participants in ranking order
export const rankingRich = computed(() =>
  ranking.value.map((r, i) => ({
    ...r,
    pos: i + 1,
    medal: i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : '',
    color: ['#F7C948','#94A3B8','#CD7F32','#60A5FA','#A78BFA','#4ADE80','#F87171','#FB923C'][i % 8],
    initial: (r.nome || '?')[0].toUpperCase(),
  }))
)

export function scoreLabel(pal, jogo) {
  if (!pal || !jogo.isFinalizado || jogo.gols_casa == null) return null
  const pts = calcPontos(pal.a, pal.b, Number(jogo.gols_casa), Number(jogo.gols_fora))
  return pts === 3 ? 'exato' : pts === 1 ? 'vencedor' : 'errou'
}
