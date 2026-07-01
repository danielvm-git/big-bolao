# BUG-2026-06-30T150000: Web ranking uses flat 3/1 scoring — missing knockout multipliers

## Problem

The bot and the web SPA show different rankings with different point totals for all players.

- **Bot** (Python): Ricardo 69pts, Flávia 54pts, Pajeh 49pts …
- **Web** (JS): Ricardo 62pts, Flávia 49pts, Pajeh 46pts …

The ordering also differs (Gisela #4 on bot vs Big #4 on web).

- **Actual behavior**: `calcPontos()` in `scoring.js` always returns 3 for exact / 1 for correct winner — ignores the phase multipliers added in commit `65d4058`.
- **Expected behavior**: Both bot and web apply the same phase-scaled scoring: R32 5/2, R16 10/5, QF 15/10, SF+3P 25/15, FIN 50/25.

**Security impact: NONE** — No security exploit path identified.

## Root Cause Analysis

Commit `65d4058` (feat(scoring): progressive Fibonacci knockout scoring, June 27 2026) added `FASE_PONTOS` to `bolao/scoring.py` and updated `bolao/ranking.py` to pass `match_id` to `pontos()`. It did **not** update `web/src/scoring.js`, leaving it with:

```js
export function calcPontos(pa, pb, ra, rb) {
  if (pa === ra && pb === rb) return 3; // ← always flat
  return s(pa, pb) === s(ra, rb) ? 1 : 0; // ← always flat
}
```

A second, related defect: `calcRanking()` detects exact matches with `if (pts === 3) e.exatos++`. Once `calcPontos` is fixed to return `5` for an R32 exact match, this condition silently stops counting exatos for knockout phases.

Python `ranking.py` correctly uses `acertou_exato(pc, pf, rc, rf)` — a pure score comparison — to track exatos independently of points.

**Risk level: High** — every player's point total is wrong in the web UI; the ordering can also be wrong.

## TDD Fix Plan

### Cycle 1 — calcPontos is phase-aware

**RED**: In `web/tests/scoring.test.js` add:

```js
// R32 exact: 5 pts
assert.strictEqual(calcPontos(2, 1, 2, 1, "R32-03"), 5);
// R32 winner: 2 pts
assert.strictEqual(calcPontos(2, 0, 3, 0, "R32-03"), 2);
// R16 exact: 10 pts
assert.strictEqual(calcPontos(1, 0, 1, 0, "R16-01"), 10);
// Group stage unchanged: 3/1
assert.strictEqual(calcPontos(1, 0, 1, 0, "R1-01"), 3);
assert.strictEqual(calcPontos(2, 0, 3, 0, "R2-04"), 1);
// No match_id → group defaults
assert.strictEqual(calcPontos(1, 0, 1, 0), 3);
```

**GREEN**: Add `FASE_PONTOS` map and optional `matchId` param to `calcPontos()`.

**verify**: `cd web && npm test`

### Cycle 2 — calcRanking exatos use score comparison, not pts===3

**RED**: Test that a R32 exact match increments exatos:

```js
const jogos = [
  { match_id: "R32-01", status: "encerrado", gols_casa: 1, gols_fora: 0 },
];
const palpites = [
  { match_id: "R32-01", telegram_id: 1, gols_casa: 1, gols_fora: 0 },
];
const parts = [{ telegram_id: 1, nome: "Ana", ativo: true }];
const r = calcRanking(jogos, palpites, parts);
assert.strictEqual(r[0].pontos, 5); // R32 exact = 5
assert.strictEqual(r[0].exatos, 1); // must be 1, not 0
```

**GREEN**: In `calcRanking()`, replace `if (pts === 3) e.exatos++` with a direct score comparison: `if (Number(p.gols_casa) === ra && Number(p.gols_fora) === rb) e.exatos++`.

**verify**: `cd web && npm test`

**REFACTOR**: None needed — the two changes are minimal and self-contained.

## Acceptance Criteria

- [ ] `calcPontos(2, 1, 2, 1, 'R32-03')` returns `5`
- [ ] `calcPontos(2, 0, 3, 0, 'R32-03')` returns `2`
- [ ] `calcPontos(1, 0, 1, 0, 'R1-01')` returns `3` (group unchanged)
- [ ] `calcPontos(1, 0, 1, 0)` (no matchId) returns `3` (default)
- [ ] `calcRanking()` counts exatos correctly for knockout phases
- [ ] Web ranking matches bot ranking for same data
- [ ] All web tests pass (`cd web && npm test`)
- [ ] All Python tests still pass (`python -m pytest tests/ -v`)

## Resolution

<!-- filled in by validate-fix -->
