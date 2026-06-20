import { test, mock } from 'node:test'
import assert from 'node:assert/strict'

// Stub global fetch — queries.js uses BB from transport.js, which calls fetch
let fetchCalls = []
let getHandler = () => Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })

mock.method(global, 'fetch', (url, opts = {}) => {
  fetchCalls.push({ url, opts })
  if (url === '/api/auth/login') {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ token: 'test-token' }),
    })
  }
  return getHandler(url, opts)
})

import { fetchJogos, fetchParticipantes, fetchAllPalpites,
  fetchPalpitesDoUsuario, savePalpite, findUser } from '../src/queries.js'

test('fetchJogos: returns sorted by kickoff', async () => {
  fetchCalls = []
  getHandler = (url) => {
    if (url.includes('/api/collections/jogos')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          data: [
            { id: 2, match_id: 'R1-02', kickoff: '2026-06-16T20:00:00Z' },
            { id: 1, match_id: 'R1-01', kickoff: '2026-06-15T20:00:00Z' },
          ],
        }),
      })
    }
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
  }
  const jogos = await fetchJogos()
  assert.equal(jogos.length, 2)
  assert.equal(jogos[0].match_id, 'R1-01')
  assert.equal(jogos[1].match_id, 'R1-02')
})

test('fetchParticipantes: returns data array', async () => {
  fetchCalls = []
  getHandler = (url) => {
    if (url.includes('/api/collections/participantes')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ data: [{ telegram_id: 111, nome: 'Alice' }] }),
      })
    }
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
  }
  const parts = await fetchParticipantes()
  assert.equal(parts.length, 1)
  assert.equal(parts[0].nome, 'Alice')
})

test('fetchAllPalpites: returns all palpites', async () => {
  fetchCalls = []
  getHandler = (url) => {
    if (url.includes('/api/collections/palpites')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          data: [{ match_id: 'R1-01', telegram_id: 111, gols_casa: 2 }],
        }),
      })
    }
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
  }
  const all = await fetchAllPalpites()
  assert.equal(all.length, 1)
})

test('fetchPalpitesDoUsuario: filters by telegram_id', async () => {
  fetchCalls = []
  getHandler = (url) => {
    if (url.includes('/api/collections/palpites')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          data: [
            { match_id: 'R1-01', telegram_id: 111, gols_casa: 2 },
            { match_id: 'R1-02', telegram_id: 222, gols_casa: 1 },
            { match_id: 'R1-03', telegram_id: 111, gols_casa: 0 },
          ],
        }),
      })
    }
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
  }
  const mine = await fetchPalpitesDoUsuario(111)
  assert.equal(mine.length, 2)
  assert.equal(mine[0].match_id, 'R1-01')
  assert.equal(mine[1].match_id, 'R1-03')
})

test('savePalpite: creates new palpite when none exists', async () => {
  fetchCalls = []
  getHandler = (url, opts) => {
    if (url.includes('/api/collections/palpites') && (!opts || opts.method !== 'POST')) {
      // GET - return empty list so no existing palpite
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ data: [] }),
      })
    }
    if (opts && opts.method === 'POST' && url === '/api/collections/palpites') {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      })
    }
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
  }
  await savePalpite('R1-01', 111, 'Alice', 2, 1)
  const postCalls = fetchCalls.filter(c => c.opts?.method === 'POST')
  assert.equal(postCalls.length, 1)
  const patchCalls = fetchCalls.filter(c => c.opts?.method === 'PATCH')
  assert.equal(patchCalls.length, 0)
})

test('savePalpite: updates existing palpite when found', async () => {
  fetchCalls = []
  getHandler = (url, opts) => {
    if (url.includes('/api/collections/palpites') && !opts?.method) {
      // GET - return existing palpite
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          data: [{ id: 'abc', match_id: 'R1-01', telegram_id: 111 }],
        }),
      })
    }
    if (opts?.method === 'PATCH') {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      })
    }
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
  }
  await savePalpite('R1-01', 111, 'Alice', 3, 0)
  const patchCalls = fetchCalls.filter(c => c.opts?.method === 'PATCH')
  assert.equal(patchCalls.length, 1)
  const postCalls = fetchCalls.filter(c => c.opts?.method === 'POST')
  assert.equal(postCalls.length, 0)
})

test('findUser: returns matching participant', async () => {
  fetchCalls = []
  getHandler = (url) => {
    if (url.includes('/api/collections/participantes')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          data: [
            { telegram_id: 111, nome: 'Alice' },
            { telegram_id: 222, nome: 'Bob' },
          ],
        }),
      })
    }
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
  }
  const user = await findUser(222)
  assert.ok(user)
  assert.equal(user.nome, 'Bob')
})

test('findUser: returns null when not found', async () => {
  fetchCalls = []
  getHandler = (url) => {
    if (url.includes('/api/collections/participantes')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ data: [{ telegram_id: 111, nome: 'Alice' }] }),
      })
    }
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
  }
  const user = await findUser(999)
  assert.equal(user, null)
})
