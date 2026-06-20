import { test } from 'node:test'
import assert from 'node:assert/strict'
import { flag } from '../src/api.js'

const WHITE = '🏳️' // fallback returned when a country has no flag

// Full World Cup 2026 roster, in the English forms the BigBase/apifootball
// feed delivers (the strings the frontend actually passes to flag()).
const TOURNAMENT_EN = [
  'South Africa', 'Germany', 'Saudi Arabia', 'Algeria', 'Argentina',
  'Australia', 'Austria', 'Belgium', 'Bosnia and Herzegovina', 'Brazil',
  'Cape Verde', 'Canada', 'Qatar', 'Colombia', 'South Korea', 'Ivory Coast',
  'Bosnia & Herzegovina',
  'Croatia', 'Curacao', 'Egypt', 'Ecuador', 'Scotland', 'Spain', 'USA',
  'France', 'Ghana', 'Haiti', 'England', 'Iran', 'Iraq', 'Japan', 'Jordan',
  'Morocco', 'Mexico', 'Norway', 'New Zealand', 'Netherlands', 'Panama',
  'Paraguay', 'Portugal', 'D.R. Congo', 'Czech Republic', 'Senegal',
  'Sweden', 'Switzerland', 'Tunisia', 'Turkey', 'Uruguay', 'Uzbekistan',
]

// Countries observed broken in production (BUG-2026-06-20-143237).
const REGRESSION = ['Iraq', 'Uzbekistan', 'Jordan', 'D.R. Congo']

test('regression: previously-broken countries resolve to a real flag', () => {
  for (const country of REGRESSION) {
    assert.notEqual(flag(country), WHITE, `${country} should have a flag`)
  }
})

test('coverage: no tournament team falls back to the white flag', () => {
  const missing = TOURNAMENT_EN.filter((c) => flag(c) === WHITE)
  assert.deepEqual(missing, [], `countries with no flag: ${missing.join(', ')}`)
})

test('normalization: punctuation, spacing and case all resolve the same', () => {
  const expected = flag('D.R. Congo')
  assert.notEqual(expected, WHITE)
  for (const variant of ['d.r. congo', 'D.R.  Congo', 'DR Congo', 'dr congo']) {
    assert.equal(flag(variant), expected, `variant "${variant}" should match`)
  }
})

test('bosnia & herzegovina (ampersand form from API) resolves to real flag', () => {
  assert.equal(flag('Bosnia & Herzegovina'), '🇧🇦', 'ampersand form should match')
  assert.equal(flag('Bosnia and Herzegovina'), '🇧🇦', 'and form should still match')
})

test('unknown country still returns the white-flag fallback', () => {
  assert.equal(flag('Atlantis'), WHITE)
  assert.equal(flag(''), WHITE)
  assert.equal(flag(undefined), WHITE)
})
