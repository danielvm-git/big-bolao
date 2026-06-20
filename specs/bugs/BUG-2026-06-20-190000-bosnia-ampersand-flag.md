# BUG-2026-06-20T190000: Bosnia & Herzegovina flag not showing

## Problem

**Actual behavior:** Bosnia & Herzegovina shows the white-flag fallback (🏳️) instead
of the country flag (🇧🇦) on the dashboard and game screens.

**Expected behavior:** Bosnia & Herzegovina should display 🇧🇦 like every other
tournament country.

**Reproduce:** 
1. Open https://bolao.bigbase.click/ 
2. Observe any game involving Bosnia & Herzegovina — the flag is 🏳️
3. Or run: `node -e "import {flag} from './src/api.js'; console.log(flag('Bosnia & Herzegovina'))"` → `"🏳️"`

## Root Cause Analysis

The frontend resolves team names to emoji flags via a static FLAGS dictionary and a
normalization function (`_normTeam`). The normalization function strips all
non-alphanumeric characters (including `&`), then collapses whitespace.

The apifootball.com API returns the team name as `"Bosnia & Herzegovina"` (with
ampersand). The normalization pipeline strips the `&`, producing `"bosnia
herzegovina"` — without the word "and" between components.

The FLAGS dictionary only has two entries for Bosnia:
- `'bosnia and herzegovina'` (EN "and" form)
- `'bosnia e herzegovina'` (PT "e" form)

Neither matches `"bosnia herzegovina"` (no connector), so the lookup falls through
to the white-flag fallback.

**Why the existing test didn't catch this:** The `TOURNAMENT_EN` list in the test
suite uses `"Bosnia and Herzegovina"` (the "and" form), not the actual `"Bosnia &
Herzegovina"` (ampersand form) that the API returns. The test coverage guard
confirms flags resolve for all listed countries, but the list didn't include the
name variant actually served in production.

**This is a recurrence of BUG-2026-06-20-143237** — that fix completed the flag
dictionary but added only the "and"/"e" connector forms, missing the "&" variant
the API uses. The normalization function's punctuation-stripping behavior (introduced
to handle "D.R. Congo") has the side effect of deleting the `&` connector for
Bosnia, which was not accounted for when adding the Bosnia entry.

**Risk level:** Low — one-line data fix. No behavioral change, just adding a missing
dictionary key.

## TDD Fix Plan

1. **RED**: Write a test asserting `flag('Bosnia & Herzegovina')` returns 🇧🇦, not 🏳️.
   **GREEN**: Add `'bosnia herzegovina':'🇧🇦'` to the FLAGS dictionary in `web/src/api.js`.
   **verify**: `cd web && node --test tests/flags.test.js`

2. **RED**: Update `TOURNAMENT_EN` in the coverage test to include `'Bosnia & Herzegovina'`
   alongside the existing `'Bosnia and Herzegovina'` — the test should fail if any
   tournament country (in either form) falls to the white flag.
   **GREEN**: The previous fix satisfies this.
   **verify**: `cd web && node --test tests/flags.test.js`

**REFACTOR**: None needed — the fix is a single dictionary addition.

## Acceptance Criteria

- [ ] `flag('Bosnia & Herzegovina')` returns 🇧🇦
- [ ] `flag('Bosnia and Herzegovina')` still returns 🇧🇦
- [ ] Coverage test includes both "Bosnia & Herzegovina" AND "Bosnia and Herzegovina"
- [ ] All new tests pass
- [ ] Existing tests still pass

## Resolution

**Fixed:** 2026-06-20
**Root cause confirmed:** API returns "Bosnia & Herzegovina" (ampersand).
`_normTeam()` strips `&` → `"bosnia herzegovina"` (no connector). FLAGS only had
`"bosnia and herzegovina"` and `"bosnia e herzegovina"` — neither matched the
stripped form.
**Fix applied:** Added `'bosnia herzegovina':'🇧🇦'` to FLAGS dictionary (1 line).
Added regression test for ampersand form + included "Bosnia & Herzegovina" in
`TOURNAMENT_EN` coverage guard.
**Hardening:** Coverage test now validates both "and" and "&" name forms.
**Evidence:** `cd web && node --test tests/flags.test.js` → 5/5 pass;
`python -m pytest tests/ -v` → 35/35 pass; manual verification confirms all
49 tournament countries resolve to real flags.
**Files changed:** `web/src/api.js`, `web/tests/flags.test.js`
