# BUG-2026-06-19-180800 — `/sync` returns 0 results (three root causes)

**Date:** 2026-06-19  
**Severity:** high  
**Scope:** bot sync, BigBase client, Telegram message formatting

## Symptoms

1. `/sync` reported "Nenhum resultado novo encontrado" despite 29 finished R1 games.
2. `/resultado R2-05 2 1` crashed with `BigBaseError: sql (403): {"error":"forbidden"}`.
3. `/lembrete` crashed with `BadRequest: Can't parse entities`.

## Root Causes

| # | Root cause |
|---|---|
| 1 | `.env` had `APIFOOTBALL_LEAGUE_ID=1` (old default); API returned "No event found" for league 1 |
| 2 | BigBase `/api/sql` endpoint returns 403 for the service account; all `bigbase.py` methods that used `self.sql()` failed silently or crashed |
| 3 | Bot username contains underscores (e.g. `jararacas_bolao_bot`); Telegram Markdown v1 parses `_` as italic, leaving unclosed entities |

## Fix Applied

1. **`APIFOOTBALL_LEAGUE_ID=1 → 28`** in `.env` (Copa 2026 league ID confirmed via `get_leagues`).  
2. **Removed all `self.sql()` usage** from `bolao/bigbase.py` — `get_jogo`, `get_participante`, `get_palpite`, `palpites_do_usuario`, `reivindicar` now use `list_records()` + client-side filter.  
3. **Switched all Telegram messages to `ParseMode.HTML`** — replaced `*bold*` with `<b>bold</b>` in `handlers.py` and `ranking.py`. HTML mode does not interpret `_` or `*` in team names or usernames.

## Hardening Added

- **`validate_config()` in `config.py`** — called at bot startup; raises `RuntimeError` if `APIFOOTBALL_KEY` or `APIFOOTBALL_LEAGUE_ID` is missing when `RESULTS_PROVIDER=apifootball`; warns if `LEAGUE_ID=1` (old default).
- **`load_dotenv(override=True)`** — prevents shell-level env vars from silently overriding `.env` values.
- **Test suite (`tests/`)** — 26 tests covering phase parsing, BRT conversion, ft-score usage, api_fixture_id matching, fallback by name, and all startup guard conditions.

## Resolution

**Fixed:** 2026-06-19  
**Root cause confirmed:** Three independent failures — wrong league ID in `.env`, forbidden SQL endpoint, Markdown parse error from underscores in bot username.  
**Fix applied:** Fixed `.env`, removed SQL from BigBase client, switched all messages to HTML.  
**Hardening added:** `validate_config()` startup guard + 26-test suite.  
**Evidence:** `python -m pytest tests/ -v` → 26 passed; live check shows `APIFOOTBALL_LEAGUE_ID='28'`, `get_jogo` works without SQL, `buscar_encerrados` found 1 new result (R2-05 2x0).  
**Commit:** `fix(bot): wrong league_id, SQL 403, Markdown parse errors — add startup guard + test suite`
