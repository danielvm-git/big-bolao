import { test, mock } from 'node:test'
import assert from 'node:assert/strict'

let fetchCalls = []
mock.method(global, 'fetch', (url, opts = {}) => {
  fetchCalls.push({ url, opts })
  if (url === '/api/collections/jogos?limit=1000') {
    return Promise.resolve({ ok: true, json: () => Promise.resolve({ data: [{ id: 1, match_id: 'R1-01' }] }) })
  }
  if (url === '/api/palpite') {
    return Promise.resolve({ ok: true, json: () => Promise.resolve({ ok: true }) })
  }
  return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
})

import { BB } from '../src/transport.js'

test('BB.get: plain GET, no credentials, no Authorization header', async () => {
  fetchCalls = []
  const result = await BB.get('/api/collections/jogos?limit=1000')
  assert.equal(fetchCalls.length, 1)
  assert.equal(fetchCalls[0].opts.headers, undefined)
  assert.deepEqual(result, { data: [{ id: 1, match_id: 'R1-01' }] })
})

test('BB.get: throws on non-ok response', async () => {
  await assert.rejects(() => BB.get('/api/collections/nonexistent'), { message: /404/ })
})

test('BB.post: sends POST with JSON body', async () => {
  fetchCalls = []
  await BB.post('/api/palpite', { match_id: 'R1-01', gols_casa: 2 })
  assert.equal(fetchCalls[0].opts.method, 'POST')
  assert.equal(fetchCalls[0].opts.headers['Content-Type'], 'application/json')
  assert.equal(JSON.parse(fetchCalls[0].opts.body).match_id, 'R1-01')
})

test('transport: never calls a login endpoint', async () => {
  fetchCalls = []
  await BB.get('/api/collections/jogos?limit=1000')
  assert.equal(fetchCalls.some(c => c.url.includes('/auth/')), false)
})
