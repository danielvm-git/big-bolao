// Re-export pure modules for backward compatibility
// New code should import directly from transport.js, queries.js, or scoring.js
export { calcPontos, calcRanking, flag, fmtDate, fmtTime, avatarColor } from './scoring.js'
export { BB } from './transport.js'

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




