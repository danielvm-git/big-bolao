# BUG-2026-06-30T140000: Wrong score for penalty-decided knockout matches

## Problem

The bot announced "Netherlands 1 x 2 Morocco" for a knockout match. The user confirmed the actual result was 1 x 1 (the score stood through all of regular time and, presumably, extra time before going to a penalty shootout).

- **Actual behavior**: Bot posts the score from `match_hometeam_score` / `match_awayteam_score` — an apifootball field that may contain an inflated or incorrect value for "After Pen." matches.
- **Expected behavior**: For penalty-decided matches, the bolão result should be the goal count from play (FT or FT+ET goals), not whatever `match_hometeam_score` carries after the penalty phase.
- **Regression**: Introduced by commit `d684eff` (fix(scoring): count 120-minute result instead of 90-minute for knockout rounds, June 28 2026).

**Security impact: NONE** — No security exploit path identified.

## Root Cause Analysis

### Background

Commit `d684eff` changed `parse_result()` in the fixtures module to prioritize `match_hometeam_score` over `match_hometeam_ft_score`. The motivation was correct: for "After ET" matches where Morocco scored in extra time, the ET result (1-2) should count rather than the 90-minute score (1-1).

### The status-blind field selection

`parse_result()` does not inspect `match_status`. It blindly prefers `match_hometeam_score` for **every** finished match, including "After Pen." status.

### apifootball field semantics

| status           | `match_hometeam_score`                                                                                                                  | `match_hometeam_ft_score` |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| Finished / FT    | Same as FT score                                                                                                                        | FT score ✓                |
| After ET / AET   | ET final score (FT + ET goals)                                                                                                          | FT score only             |
| After Pen. / PEN | **Unreliable** — may reflect a transient live score, partial penalty tally, or API quirk; not guaranteed to equal the actual goal count | FT score ✓                |

For a match like Netherlands vs Morocco that ended 1-1 at 90 min, was still 1-1 after ET, and Morocco won on penalties:

- `match_hometeam_ft_score` = "1" (correct)
- `match_awayteam_ft_score` = "1" (correct)
- `match_hometeam_score` = "1" (should be 1 but may be wrong)
- `match_awayteam_score` = "2" ← **apifootball returned "2" here, causing the bug**

The previous code (before `d684eff`) would have read `match_hometeam_ft_score` ("1") and reported the correct 1 x 1. The new code reads `match_hometeam_score` ("2") and posts the wrong 1 x 2.

### Why the fix for "After ET" was correct but overcorrected

The group vote (June 28 2026) decided ET goals count. That means:

- "After ET": Morocco scored 1 in ET → `match_awayteam_score` = "2" is **correct** and should be used.
- "After Pen.": No goals in ET → `match_awayteam_score` should still be "1", but the API may return "2" for reasons outside our control.

The fix should be **status-aware**: use `match_*_score` (ET total) only for "After ET" statuses; use `match_*_ft_score` for penalty-decided matches.

**Risk level: High** — affects all knockout matches decided on penalties; scores get stored wrongly in BigBase and cannot be corrected automatically.

## Immediate Data Correction (before or alongside the code fix)

The wrong score is already stored in BigBase as `gols_fora=2` for the Netherlands vs Morocco match. Because `buscar_encerrados()` skips games with `status=encerrado`, re-running `/sync` will NOT overwrite it — even after the code is fixed. The admin must correct it manually:

```
/resultado <match_id> 1 1
```

`<match_id>` is the R32 identifier for Netherlands vs Morocco (e.g. `R32-03`). Find it from the BigBase dashboard at https://bigbase.click/admin or by running `/meus` to see bets with their match IDs.

**What this does:**

- Calls `set_resultado(match_id, 1, 1)` → patches `gols_casa=1`, `gols_fora=1`, `status=encerrado` in BigBase
- Reposts "Fim de jogo: Netherlands 1 x 1 Morocco" to the group with the correct cravadores

**After that, post the corrected ranking:**

- Run `/ranking` in the group to show the updated points (the ranking calculates dynamically from stored scores, so it will be correct once the score is fixed)

Note: points are not stored — `ranking.calcular()` recomputes them live from the `jogos` and `palpites` records, so fixing the score in BigBase is sufficient to restore the full ranking.

## TDD Fix Plan

### Cycle 1 — Penalty matches use FT score, not match\_\*\_score

**RED**: Write a test in `test_fixtures.py` (and mirror in `test_results.py`):

```python
def test_pen_match_uses_ft_score_not_match_score():
    """After Pen. match: parse_result uses ft_score, not match_*_score."""
    fx = {
        "match_status": "After Pen.",
        "match_hometeam_score": "1",
        "match_awayteam_score": "2",   # API quirk / wrong value
        "match_hometeam_ft_score": "1",
        "match_awayteam_ft_score": "1",
    }
    assert parse_result(fx) == (1, 1)
```

**GREEN**: In `parse_result()`, check `fixture.get("match_status")`. For statuses in `{"After Pen.", "PEN", "Finished PEN"}`, use `match_hometeam_ft_score` as the primary field (with `match_hometeam_score` as fallback). Keep the current (ET-first) logic for all other statuses.

**verify**: `python -m pytest tests/test_fixtures.py -v -k "pen"`

### Cycle 2 — "After ET" still uses ET score

**RED**: Confirm existing `test_uses_et_score_not_ft_score` in `test_results.py` still passes (it uses status "After ET"):

```python
# Already in test_results.py — must remain green after the fix
"match_status": "After ET",
"match_hometeam_score": "2",   # ET score — must be used
"match_awayteam_score": "1",
"match_hometeam_ft_score": "1",
"match_awayteam_ft_score": "1",
```

**GREEN**: The Cycle 1 change must not affect "After ET" — those still use `match_hometeam_score`.

**verify**: `python -m pytest tests/test_fixtures.py tests/test_results.py -v`

### Cycle 3 — "PEN" and "Finished PEN" aliases also handled

**RED**: Test that the two alias statuses for penalty matches also trigger FT-score logic:

```python
@pytest.mark.parametrize("status", ["After Pen.", "PEN", "Finished PEN"])
def test_all_pen_statuses_use_ft_score(status):
    fx = {
        "match_status": status,
        "match_hometeam_score": "99", "match_awayteam_score": "99",
        "match_hometeam_ft_score": "1", "match_awayteam_ft_score": "1",
    }
    assert parse_result(fx) == (1, 1)
```

**GREEN**: The set of penalty statuses in `parse_result()` must include all three.

**verify**: `python -m pytest tests/test_fixtures.py -v -k "pen_statuses"`

**REFACTOR**: Update the docstring of `parse_result()` to document the status-aware field selection and the reason for the split (apifootball `match_hometeam_score` is unreliable for "After Pen." matches).

## Acceptance Criteria

**Data correction (immediate):**

- [ ] Admin runs `/resultado <R32-match-id> 1 1` to overwrite the wrong score in BigBase
- [ ] Group sees a corrected "Fim de jogo: Netherlands 1 x 1 Morocco" announcement
- [ ] Admin runs `/ranking` to post the recalculated ranking

**Code fix:**

- [ ] `parse_result()` returns (1, 1) for a fixture with `match_status="After Pen."`, `match_*_score="1"/"2"`, `match_*_ft_score="1"/"1"`
- [ ] `parse_result()` returns (2, 1) for a fixture with `match_status="After ET"`, `match_*_score="2"/"1"`, `match_*_ft_score="1"/"1"` (ET goal counts)
- [ ] All three penalty aliases handled: "After Pen.", "PEN", "Finished PEN"
- [ ] All 3 new tests pass
- [ ] All existing tests still pass (`python -m pytest tests/ -v`)

## Resolution

- **Fixed**: 2026-06-30
- **Approach**: Added `_PEN_STATUSES` frozenset to `fixtures.py`; `parse_result()` now checks `match_status` before choosing field — penalty statuses use `match_*_ft_score`, all others keep ET-first logic.
- **Tests added**: 5 (4 new RED→GREEN + 1 guard for After ET regression)
- **Suite**: 115/115 pass
