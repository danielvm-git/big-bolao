// I/O transport layer — HTTP client for BigBase API.

export const BB = {
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
