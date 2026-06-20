/**
 * BigBase API client for the Bolão web app.
 *
 * Calls BigBase REST API directly using a JWT token.
 * For production, this will use magic-link auth + BigBase Functions.
 * For dev/testing, uses a service-account JWT from env vars.
 */

const BB = {
  url: '',
  _token: null,

  async _ensureToken() {
    if (BB._token) return
    const r = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'bolao-bot@bigbase.local', password: 'bolao-bot-secure-password-2026' }),
    })
    if (r.ok) BB._token = (await r.json()).token
  },

  async _headers() {
    await BB._ensureToken()
    return {
      'Content-Type': 'application/json',
      ...(BB._token ? { Authorization: `Bearer ${BB._token}` } : {}),
    }
  },

  async _fetch(path, opts = {}) {
    const res = await fetch(`${BB.url}${path}`, {
      headers: await BB._headers(),
      ...opts,
    })
    if (!res.ok) {
      const body = await res.text().catch(() => '')
      throw new Error(`BigBase ${res.status}: ${body.slice(0, 200)}`)
    }
    return res.json()
  },

  /** List all records in a collection */
  async list(collection) {
    const res = await BB._fetch(`/api/collections/${collection}?limit=500`)
    return res.data || []
  },

  /** Run a read-only SQL query */
  async sql(query) {
    const res = await BB._fetch('/api/sql', {
      method: 'POST',
      body: JSON.stringify({ query }),
    })
    // /api/sql returns { columns: [...], rows: [...] }
    const cols = res.columns || []
    const rows = res.rows || []
    // If rows are objects, use as-is; otherwise zip with columns
    return rows.length && typeof rows[0] === 'object'
      ? rows
      : rows.map(row => Object.fromEntries(cols.map((c, i) => [c, row[i]])))
  },

  /** Create a record in a collection */
  async create(collection, data) {
    const res = await BB._fetch(`/api/collections/${collection}`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
    return res.id
  },

  /** Patch a record */
  async patch(collection, id, data) {
    await BB._fetch(`/api/collections/${collection}/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },
}

// ─── High-level API ───────────────────────────────────────────

export async function fetchJogos() {
  const rows = await BB.list('jogos')
  return rows.sort((a, b) => (a.kickoff || '').localeCompare(b.kickoff || ''))
}

export async function fetchParticipantes() {
  return BB.list('participantes')
}

export async function fetchPalpites(telegramId) {
  const all = await BB.list('palpites')
  return all
    .filter(p => Number(p.telegram_id) === Number(telegramId))
    .map(p => ({ ...p, _rowid: p.id }))
}

export async function fetchAllPalpites() {
  return BB.list('palpites')
}

export async function savePalpite(matchId, telegramId, nome, golsCasa, golsFora) {
  // Check if prediction already exists (fetch all, filter client-side)
  const all = await BB.list('palpites')
  const existing = all.find(
    p => String(p.match_id) === String(matchId) &&
         Number(p.telegram_id) === Number(telegramId)
  )

  const payload = {
    match_id: matchId,
    telegram_id: Number(telegramId),
    nome,
    gols_casa: golsCasa,
    gols_fora: golsFora,
    atualizado_em: new Date().toISOString(),
  }

  if (existing) {
    await BB.patch('palpites', existing.id, payload)
  } else {
    await BB.create('palpites', payload)
  }
}

// ─── Pontuação (client-side mirror of bolao/scoring.py) ──────

export function calcPontos(palpiteCasa, palpiteFora, realCasa, realFora) {
  if (palpiteCasa === realCasa && palpiteFora === realFora) return 3
  const sinal = (a, b) => (a > b ? 1 : a < b ? -1 : 0)
  if (sinal(palpiteCasa, palpiteFora) === sinal(realCasa, realFora)) return 1
  return 0
}

// ─── Ranking (client-side mirror of bolao/ranking.py) ─────────

export function calcRanking(jogos, palpites, participantes) {
  const nomes = {}
  for (const p of participantes) {
    nomes[Number(p.telegram_id)] = p.nome || '?'
  }

  const encerrados = {}
  for (const j of jogos) {
    if (j.status === 'encerrado' && j.gols_casa != null) {
      encerrados[j.match_id] = [Number(j.gols_casa), Number(j.gols_fora)]
    }
  }

  const acc = {}
  for (const p of palpites) {
    if (!encerrados[p.match_id]) continue
    const tid = Number(p.telegram_id)
    const [rc, rf] = encerrados[p.match_id]
    const pts = calcPontos(Number(p.gols_casa), Number(p.gols_fora), rc, rf)
    const e = acc[tid] || (acc[tid] = { telegram_id: tid, pontos: 0, exatos: 0, acertos: 0, jogos: 0 })
    e.pontos += pts
    e.jogos += 1
    if (pts === 3) e.exatos++
    if (pts >= 1) e.acertos++
  }

  // Ensure all participants appear
  for (const [tid, nome] of Object.entries(nomes)) {
    if (!acc[tid]) acc[tid] = { telegram_id: Number(tid), pontos: 0, exatos: 0, acertos: 0, jogos: 0 }
  }

  for (const [tid, e] of Object.entries(acc)) {
    e.nome = nomes[Number(tid)] || String(tid)
  }

  return Object.values(acc).sort((a, b) =>
    b.pontos - a.pontos || b.exatos - a.exatos || a.nome.localeCompare(b.nome)
  )
}

export { BB }
