# BUG-2026-07-30-100000: format_resultado hardcodes == 3 for cravadores

## Summary

`format_resultado` in `group_publisher.py` used `pontos(...) == 3` to detect exact-match predictions ("cravadores"). This only works for group-stage matches where exact = 3 pts. Knockout matches have different exact values (R32=5, R16=10, QF=15, SF/3P=25, FIN=50), so knockout exact scorers were never announced in the group.

## Root Cause

The function was written before knockout phase scoring existed. When `FASE_PONTOS` was added, `format_resultado` was not updated — it continued to check `== 3` instead of using `acertou_exato()`.

## Fix

Replaced `pontos(...) == 3` with `acertou_exato(...)` — a phase-agnostic exact score check.

## Files Changed

- `bolao/group_publisher.py` — import changed from `pontos` to `acertou_exato`; cravadores detection updated
- `tests/test_group_publisher.py` — added `test_knockout_exact_still_announced_as_cravou` regression test

## Verification

- 168 Python tests pass (including new regression test)
- 89 web tests pass
- G1/G2/G3 governance all PASS
