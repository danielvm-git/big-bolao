---
bug_id: BUG-2026-07-07-183300-ci-g3-fixtures-config-import
status: fixed
fixed_date: "2026-07-07"
severity: high
scope: ci
title: G3 coverage gate fails — fixtures imports config requiring TELEGRAM_TOKEN
---

# BUG-2026-07-07-183300: G3 coverage gate fails on fixtures import

## Problem

CI run [28889506975](https://github.com/danielvm-git/big-bolao/actions/runs/28889506975) failed at **Check P0 coverage** (G3 gate):

```
ERROR collecting tests/test_fixtures.py
bolao/fixtures.py:25: in <module>
    from bolao import config
bolao/config.py:14: in <module>
    TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
KeyError: 'TELEGRAM_TOKEN'
```

The full Python test suite passed earlier in the same job because that step sets `TELEGRAM_TOKEN`, `BIGBASE_EMAIL`, and `BIGBASE_PASSWORD`. The G3 coverage step runs three isolated `pytest --cov` commands without those env vars.

**Security impact:** NONE — CI misconfiguration, no exploit path.

## Root cause

`bolao/fixtures.py` added `from bolao import config` (for `fetch_from_api` to read `APIFOOTBALL_KEY` / `APIFOOTBALL_LEAGUE_ID`). Importing `bolao.config` eagerly reads `TELEGRAM_TOKEN` and `BIGBASE_EMAIL`/`BIGBASE_PASSWORD` at module load time.

Pure fixture helpers (`parse_result`, `normalise`, `_parse_phase`) should not require bot credentials to import. CI G3 runs coverage on `test_fixtures.py` without the bot env block.

## Fix approach

1. **Code:** Remove top-level `config` import from `fixtures.py`; read `APIFOOTBALL_KEY` and `APIFOOTBALL_LEAGUE_ID` via `os.environ.get` inside `fetch_from_api` only.
2. **CI (belt-and-suspenders):** Add the same test env vars to the G3 coverage step as the main Python test step.
3. **Test:** Subprocess regression test — import `bolao.fixtures` from a cwd with no `.env` and no bot credentials.

**Risk:** Low — `fetch_from_api` behavior unchanged; only import coupling removed.

## TDD plan

| Step | RED                                                                           | GREEN                                                            |
| ---- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| 1    | `test_fixtures_imports_without_bot_credentials` fails (subprocess, clean env) | Remove `config` import; use `os.environ.get` in `fetch_from_api` |
| 2    | —                                                                             | Add CI env vars to G3 step in `.github/workflows/ci-cd.yml`      |

## Verify

→ verify: `cd /tmp && env -i PATH="$PATH" HOME="$HOME" PYTHONPATH="$PWD" python3 -c "from bolao.fixtures import parse_result"`

→ verify: `python -m pytest tests/test_fixtures.py -q`

→ verify: `python -m pytest --cov=bolao.fixtures --cov-fail-under=90 tests/test_fixtures.py -q` (without TELEGRAM_TOKEN in env, from /tmp cwd via subprocess test)
