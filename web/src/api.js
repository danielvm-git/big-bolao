// Re-export pure modules for backward compatibility
// New code should import directly from transport.js, queries.js, or scoring.js
export { calcPontos, flag } from './scoring.js'

// BigBase API client — auto-authenticates with service account
const BB = {
  _token: null,

  async _auth() {
    if (BB._token) return
    const r = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'bolao-bot@bigbase.local', password: 'bolao-bot-secure-password-2026' }),
    })
    if (r.ok) BB._token = (await r.json()).token
  },

  async get(path) {
    await BB._auth()
    const r = await fetch(path, { headers: { Authorization: `Bearer ${BB._token}` } })
    if (!r.ok) throw new Error(`${r.status} ${path}`)
    return r.json()
  },

  async post(path, body) {
    await BB._auth()
    const r = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${BB._token}` },
      body: JSON.stringify(body),
    })
    if (!r.ok) throw new Error(`${r.status} ${path}`)
    return r.json()
  },

  async patch(path, body) {
    await BB._auth()
    const r = await fetch(path, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${BB._token}` },
      body: JSON.stringify(body),
    })
    if (!r.ok) throw new Error(`${r.status} ${path}`)
  },
}

async function list(col) {
  const d = await BB.get(`/api/collections/${col}?limit=1000`)
  return d.data || []
}

export async function fetchJogos() {
  const rows = await list('jogos')
  return rows.sort((a, b) => (a.kickoff || '').localeCompare(b.kickoff || ''))
}

export async function fetchParticipantes() {
  return list('participantes')
}

export async function fetchAllPalpites() {
  return list('palpites')
}

export async function fetchPalpitesDoUsuario(telegramId) {
  const all = await list('palpites')
  return all.filter(p => Number(p.telegram_id) === Number(telegramId))
}

export async function savePalpite(matchId, telegramId, nome, golsCasa, golsFora) {
  const all = await list('palpites')
  const ex = all.find(p => String(p.match_id) === String(matchId) && Number(p.telegram_id) === Number(telegramId))
  const payload = { match_id: matchId, telegram_id: Number(telegramId), nome, gols_casa: golsCasa, gols_fora: golsFora, atualizado_em: new Date().toISOString() }
  if (ex) await BB.patch(`/api/collections/palpites/${ex.id}`, payload)
  else await BB.post('/api/collections/palpites', payload)
}

export async function findUser(telegramId) {
  const parts = await list('participantes')
  return parts.find(p => Number(p.telegram_id) === Number(telegramId)) || null
}

export function calcRanking(jogos, palpites, participantes) {
  const ativos = participantes.filter(p => p.ativo !== false && Number(p.telegram_id) > 0)
  const nomes = Object.fromEntries(ativos.map(p => [Number(p.telegram_id), p.nome || '?']))
  const enc = {}
  for (const j of jogos) {
    if (j.status === 'encerrado' && j.gols_casa != null)
      enc[j.match_id] = [Number(j.gols_casa), Number(j.gols_fora)]
  }
  const acc = {}
  for (const p of palpites) {
    const tid = Number(p.telegram_id)
    if (!nomes[tid] || !enc[p.match_id]) continue
    const [ra, rb] = enc[p.match_id]
    const pts = calcPontos(Number(p.gols_casa), Number(p.gols_fora), ra, rb)
    const e = acc[tid] || (acc[tid] = { telegram_id: tid, nome: nomes[tid], pontos: 0, exatos: 0, acertos: 0 })
    e.pontos += pts
    if (pts === 3) e.exatos++
    if (pts >= 1) e.acertos++
  }
  for (const tid of Object.keys(nomes)) {
    if (!acc[tid]) acc[Number(tid)] = { telegram_id: Number(tid), nome: nomes[tid], pontos: 0, exatos: 0, acertos: 0 }
  }
  return Object.values(acc).sort((a, b) => b.pontos - a.pontos || b.exatos - a.exatos || a.nome.localeCompare(b.nome))
}

export function fmtDate(iso) {
  if (!iso) return ''
  const [,m,d] = iso.split('T')[0].split('-')
  return `${d}/${m}`
}
export function fmtTime(iso) {
  if (!iso) return ''
  return iso.split('T')[1]?.slice(0,5) || ''
}

const COLORS = ['#F7C948','#94A3B8','#CD7F32','#60A5FA','#A78BFA','#4ADE80','#F87171','#FB923C']
export function avatarColor(i) { return COLORS[i % COLORS.length] }
