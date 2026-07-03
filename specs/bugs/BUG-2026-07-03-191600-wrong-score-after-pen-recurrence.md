# BUG-2026-07-03T191600: Wrong score for penalty-decided knockout match (recurrence)

## Problem

The bot announced "Australia 1 x 2 Egypt" for a knockout match (R32). The actual result was 1 x 1 after extra time (120 min), with Egypt winning on penalties. The API returned an inflated `match_awayteam_score` ("2") — the +1 representing the penalty shootout win — and the bot read it instead of `match_awayteam_ft_score` ("1").

- **Actual behavior**: Bot posts "Australia 1 x 2 Egypt"
- **Expected behavior**: Bot posts "Australia 1 x 1 Egypt" (score at end of 120 min)
- **Regression**: Same root cause as BUG-2026-06-30-140000 (Netherlands vs Morocco). The previous fix was incomplete.

**Security impact: NONE**

## Root Cause Analysis

### Previous fix (15b8c8d) was fragile

The fix for BUG-2026-06-30-140000 used a **whitelist** approach:

```python
_PEN_STATUSES = frozenset({"After Pen.", "PEN", "Finished PEN"})

if status in _PEN_STATUSES:
    use ft_score  # safe
else:
    use match_score  # dangerous (default path!)
```

If apifootball returns **any** status string not in `_PEN_STATUSES` for a penalty-decided match — e.g., `"Finished"`, a new variant, or any string we haven't seen — the code falls through to the `else` branch and reads the unreliable `match_score` field.

### apifootball field semantics (unchanged)

| status           | `match_score`                                             | `ft_score` |
| ---------------- | --------------------------------------------------------- | ---------- |
| After ET / AET   | Correct (FT + ET goals)                                   | FT only    |
| After Pen. / PEN | **Unreliable** — may be inflated by +1 for penalty winner | Correct    |
| Finished / FT    | Same as ft_score (no extra time)                          | Correct    |

### Why the whitelist approach is wrong

The API status strings can vary. The `_PEN_STATUSES` set must enumerate every possible penalty status — but the API may return variants we haven't encountered. Missing one causes the bug to recur. A **denylist** approach is safer: only ET statuses get `match_score`; everything else gets `ft_score`.

## Fix

Invert the logic in `parse_result()`:

**Before (whitelist — fragile):**

```python
_PEN_STATUSES = frozenset({"After Pen.", "PEN", "Finished PEN"})

if status in _PEN_STATUSES:
    gh = ft_score or match_score
else:
    gh = match_score or ft_score   # ← default is dangerous
```

**After (denylist — safe):**

```python
_ET_STATUSES = frozenset({"After ET", "AET", "Finished AET"})

if status in _ET_STATUSES:
    gh = match_score or ft_score
else:
    gh = ft_score or match_score   # ← default is safe
```

Unknown/unexpected statuses now default to `ft_score` — the reliable field.

## Immediate Data Correction

The wrong score is already stored in BigBase. Because `/sync` skips games with `status=encerrado`, re-running it will NOT overwrite. Admin must correct manually:

```
/resultado <match_id> 1 1
```

Where `<match_id>` is the R32 identifier for Australia vs Egypt. After correction, run `/ranking` to recalculate points.

## Acceptance Criteria

- [x] `parse_result()` defaults to `ft_score` for ALL non-ET statuses (penalty, regular, unknown future)
- [x] `parse_result()` still uses `match_score` for ET statuses (ET goals count)
- [x] All 127 tests pass
- [x] Behavioral proof: Australia-Egypt scenario returns (1,1); After ET returns (2,1); unknown status safe
- [x] Type check: `bolao/fixtures.py` passes mypy
- [x] Lint: flake8 clean
- [x] Hardening: warning log on match_score ≠ ft_score discrepancy
- [ ] Admin corrects Australia x Egypt score in BigBase: `/resultado R32-14 1 1`

## Resolution

- **Fixed**: 2026-07-03
- **Root cause confirmed**: `_PEN_STATUSES` whitelist missed the API's actual status string ("Finished") for Australia vs Egypt. Non-ET statuses fell through to unreliable `match_score`.
- **Fix**: Replaced `_PEN_STATUSES` whitelist with `_ET_STATUSES` denylist. Only "After ET" / "AET" / "Finished AET" read `match_score`; everything else defaults to safe `ft_score`.
- **Hardening added**: Warning log when `match_score` ≠ `ft_score` for non-ET statuses — catches future API status-string drift before it corrupts scores.
- **Evidence**: 127/127 tests pass, behavioral proof confirms (1,1) for Australia-Egypt scenario.
- **Commit**: `fix(scoring): default parse_result to ft_score — only ET statuses use match_score`
