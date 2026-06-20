import { test, mock } from 'node:test'
import assert from 'node:assert/strict'

// Stub global fetch before importing transport
let fetchCalls = []
mock.method(global, 'fetch', (url, opts = {}) => {
  fetchCalls.push({ url, opts })
  if (url === '/api/auth/login') {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ token: 'test-token-123' }),
    })
  }
  if (url === '/api/collections/jogos?limit=1000') {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ data: [{ id: 1, match_id: 'R1-01' }] }),
    })
  }
  if (url === '/api/collections/palpites') {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({}),
    })
  }
  // PATCH to a specific palpite
  if (url === '/api/collections/palpites/abc') {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({}),
    })
  }
  // Default error response
  return Promise.resolve({
    ok: false,
    status: 404,
    json: () => Promise.resolve({}),
  })
})

import { BB } from '../src/transport.js'

test('BB._auth: logs in with service account and stores token', async () => {
  fetchCalls = []
  BB._token = null
  await BB._auth()
  const loginCall = fetchCalls.find(c => c.url === '/api/auth/login')
  assert.ok(loginCall, 'should call /api/auth/login')
  assert.equal(loginCall.opts.method, 'POST')
  assert.equal(JSON.parse(loginCall.opts.body).email, 'bolao-bot@bigbase.local')
  assert.equal(BB._token, 'test-token-123')
})

test('BB._auth: skips login if token already exists', async () => {
  fetchCalls = []
  BB._token = 'existing-token'
  await BB._auth()
  const loginCall = fetchCalls.find(c => c.url === '/api/auth/login')
  assert.equal(loginCall, undefined, 'should not call auth again')
})

test('BB.get: sends GET with Authorization header', async () => {
  fetchCalls = []
  BB._token = 't'
  const result = await BB.get('/api/collections/jogos?limit=1000')
  const call = fetchCalls.find(c => c.url === '/api/collections/jogos?limit=1000')
  assert.ok(call)
  assert.equal(call.opts.method || 'GET', 'GET')
  assert.equal(call.opts.headers?.Authorization, 'Bearer t')
  assert.deepEqual(result, { data: [{ id: 1, match_id: 'R1-01' }] })
})

test('BB.get: throws on non-ok response', async () => {
  await assert.rejects(
    () => BB.get('/api/collections/nonexistent'),
    { message: /404/ }
  )
})

test('BB.post: sends POST with JSON body', async () => {
  fetchCalls = []
  BB._token = 't'
  await BB.post('/api/collections/palpites', { match_id: 'R1-01', gols_casa: 2 })
  const call = fetchCalls.find(c => c.url === '/api/collections/palpites')
  assert.ok(call)
  assert.equal(call.opts.method, 'POST')
  assert.equal(call.opts.headers['Content-Type'], 'application/json')
  assert.equal(JSON.parse(call.opts.body).match_id, 'R1-01')
})

test('BB.patch: sends PATCH with JSON body', async () => {
  fetchCalls = []
  BB._token = 't'
  await BB.patch('/api/collections/palpites/abc', { gols_casa: 3 })
  const call = fetchCalls.find(c => c.url === '/api/collections/palpites/abc')
  assert.ok(call)
  assert.equal(call.opts.method, 'PATCH')
  assert.equal(call.opts.headers['Content-Type'], 'application/json')
})

test('BB._auth: called automatically by get when no token', async () => {
  fetchCalls = []
  BB._token = null
  const result = await BB.get('/api/collections/jogos?limit=1000')
  const authCall = fetchCalls.find(c => c.url === '/api/auth/login')
  assert.ok(authCall, '_auth should be called automatically')
  assert.ok(result, 'should return data')
})
