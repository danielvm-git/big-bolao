---
bug_id: BUG-2026-07-13-225800
status: resolved
severity: low
scope: web/scoring
title: "Inglaterra missing flag — Portuguese name not in FLAGS dict"
---

## Problem

England shows no flag (white fallback 🏳️) in the web UI when the team name is in Portuguese ("Inglaterra"). The FLAGS dict in `web/src/scoring.js` only has the English key `england`, not the Portuguese `inglaterra`.

This affects manually-created knockout matches (SF-02, future 3P/FIN) where BigBase stores Portuguese team names from the `matches.py` seed fallback.

## Root Cause Analysis

- `FLAGS` dict maps normalized team names → emoji flags
- `_normTeam()` strips accents but does NOT translate languages
- `inglaterra` normalizes to `inglaterra` (no accents to strip)
- Lookup for `inglaterra` in FLAGS → miss → white flag fallback
- All other Portuguese names used in `matches.py` (França, Espanha, etc.) had corresponding entries — `inglaterra` was the only one missing

## Fix

Added `inglaterra: "🏴󠁧󠁢󠁥󠁮󠁧󠁿"` to FLAGS dict in `web/src/scoring.js`.

## TDD Fix Plan

1. **RED**: Add test for Portuguese team names from manual knockout seeds
   **GREEN**: Add `inglaterra` key to FLAGS dict
   **verify**: `cd web && node --test tests/flags.test.js`

## Acceptance Criteria

- [x] `flag('Inglaterra')` returns 🏴󠁧󠁢󠁥󠁮󠁧󠁿 (not 🏳️)
- [x] All 89 web tests pass
- [x] All 167 Python tests pass
- [x] Web dist rebuilt

## Resolution

Fixed in `web/src/scoring.js` + test in `web/tests/flags.test.js`.
