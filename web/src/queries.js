// Domain query functions — consume BB from transport.js.

import { BB, session } from './transport.js'

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

// The server checks the signed link, that the match is open, and takes the
// name from its own records. `nome` stays in the signature for callers.
// eslint-disable-next-line no-unused-vars
export async function savePalpite(matchId, telegramId, nome, golsCasa, golsFora) {
  await BB.post('/api/palpite', {
    uid: Number(telegramId), sig: session.sig,
    match_id: matchId, gols_casa: golsCasa, gols_fora: golsFora,
  })
}

export async function findUser(telegramId) {
  const parts = await list('participantes')
  return parts.find(p => Number(p.telegram_id) === Number(telegramId)) || null
}
