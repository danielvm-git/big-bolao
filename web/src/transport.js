// I/O transport layer — HTTP client for the bolao server API.
// The browser holds no store credentials: the server owns the data.
// `session` carries the signed link (?uid=&sig=) the bot sent this user.

export const session = { uid: null, sig: null }

export const BB = {
  async get(path) {
    const r = await fetch(path)
    if (!r.ok) throw new Error(`${r.status} ${path}`)
    return r.json()
  },

  async post(path, body) {
    const r = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!r.ok) throw new Error(`${r.status} ${path}`)
    return r.json()
  },
}
