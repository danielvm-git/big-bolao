import { test } from 'node:test'
import assert from 'node:assert/strict'
import { calcPontos } from '../src/scoring.js'

// Scoring rules: 3 = exact score, 1 = correct winner/draw, 0 = miss
test('calcPontos: exact match returns 3', () => {
  assert.equal(calcPontos(2, 1, 2, 1), 3)
  assert.equal(calcPontos(0, 0, 0, 0), 3)
  assert.equal(calcPontos(5, 3, 5, 3), 3)
})

test('calcPontos: correct winner (but not exact) returns 1', () => {
  // Casa wins: palpite 2-1, real 1-0 → same sign (+1)
  assert.equal(calcPontos(2, 1, 1, 0), 1)
  // Fora wins: palpite 0-2, real 1-3 → same sign (-1)
  assert.equal(calcPontos(0, 2, 1, 3), 1)
  // Draw: palpite 1-1, real 2-2 → same sign (0)
  assert.equal(calcPontos(1, 1, 2, 2), 1)
})

test('calcPontos: wrong outcome returns 0', () => {
  // Palpite casa wins, real fora wins
  assert.equal(calcPontos(2, 0, 0, 2), 0)
  // Palpite draw, real casa wins
  assert.equal(calcPontos(1, 1, 2, 0), 0)
  // Palpite fora wins, real draw
  assert.equal(calcPontos(0, 1, 1, 1), 0)
})
