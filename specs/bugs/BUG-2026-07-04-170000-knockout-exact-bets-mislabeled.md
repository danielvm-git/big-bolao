# BUG-2026-07-04-170000: Knockout exact bets mislabeled as "acertei"

## Status: fixed

## Description
In the web SPA (`web/src/store.js::scoreLabel()`), bets on knockout-phase
matches that are exact score hits display as "acertei" instead of "exato".
This happens because `calcPontos()` is called **without** `matchId`, so it
defaults to group-phase scoring thresholds (3 for exact, 1 for winner). Since
knockout exact bets score 5–50 points (not 3), the comparison `pts === 3`
never matches.

## Root Cause
`store.js` line 85: `calcPontos(pal.a, pal.b, Number(jogo.gols_casa), Number(jogo.gols_fora))`
— missing the 5th argument `jogo.match_id`.

## Fix
1. Extracted `scoreLabelFor(pa, pb, ra, rb, matchId)` as a pure function in
   `web/src/scoring.js` that calls `calcPontos(pa, pb, ra, rb, matchId)` and
   returns `"exato"` / `"vencedor"` / `"errou"` based on exact-match or
   sign-match, independent of point thresholds.
2. Updated `web/src/store.js::scoreLabel()` to delegate, passing
   `jogo.match_id`.

## Tests Added
- Golden fixture `scoring-golden.json` now includes `expected_label` field for
  all 24 cases.
- `web/tests/scoring-golden.test.js` runs `scoreLabelFor()` against each case.
- All 49 golden tests pass (25 × calcPontos + 24 × scoreLabelFor).
- Confirmed via golden suite: all knockout exact cases now label as "exato".

## Verification
- 88 web tests pass (including golden suite with label assertions).
- 153 Python tests pass (unchanged).
- `web/dist/` rebuilt.
