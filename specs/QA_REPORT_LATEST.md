# QA Audit Report — big-bolao

Generated: 2026-07-30

## Run Config

### N (Bug Ceiling)

- **Floor**: 3 confirmed open bugs (BUG-2026-06-19-190000, BUG-2026-06-21-104800, BUG-2026-07-15-120400)
- **Ceiling**: 15 (repo ~7.5k LOC Python+JS → 15 per scaling rule)
- **N = 15**

### FROZEN (Contracts)

| Item                                           | Source                          | Reason                                      |
| ---------------------------------------------- | ------------------------------- | ------------------------------------------- |
| `specs/test-strategy/scoring-golden.json`      | CONVENTIONS.md §Golden fixtures | Shared Python↔JS truth — 24 scoring cases   |
| `specs/test-strategy/parse-result-golden.json` | CONVENTIONS.md §Golden fixtures | Shared Python↔JS truth — 17 parse cases     |
| `scripts/check_scoring_tables.py`              | CI governance G2                | Enforces FASE_PONTOS parity                 |
| `scripts/check_test_governance.py`             | CI governance G1                | Enforces bug registry completeness          |
| `bolao/config.py::validate_config()`           | CONVENTIONS.md §Code            | Startup guard — never bypass                |
| `bolao/logger.py::JSONFormatter`               | CONVENTIONS.md §Code            | Structured logging contract                 |
| `app.py` entry point                           | AGENTS.md §Architecture         | BigBase deployment contract ($PORT, thread) |
| `ParseMode.HTML`                               | AGENTS.md §Known Issues         | Telegram messages — never Markdown          |
| `FASE_PONTOS` (Python + JS)                    | G2 governance, CONVENTIONS.md   | 6-phase scoring — parity enforced           |
| `MATCHES` dict (72 games)                      | AGENTS.md §Architecture         | Hardcoded schedule — matches API            |

### Hotspots (churn × fix density)

1. `bolao/ranking.py` (20 commits, multiple format regressions)
2. `bolao/handlers.py` (11 commits, god-module refactored)
3. `bolao/bigbase.py` (11 commits, auth/setup lifecycle)
4. `bolao/fixtures.py` (9 commits, parse_result regressions ×2)
5. `app.py` (14 commits, deploy/startup issues)
6. `web/src/App.vue` (12 commits, nav/routing bugs)
7. `web/src/api.js` (11 commits, refactored into modules)
8. `.github/workflows/ci-cd.yml` (19 commits, CI pipeline)

### Seeded Issue Numbers

- #18: CI/CD Template Consolidation (enhancement, open)
- #19: Update GitHub Actions to latest versions (open)
- #24: pytest-asyncio update (PR, CI failing on verify — merge commit format)

### Existing Bug Registry

- 25 bugs total (22 fixed, 3 open)
- Open: BUG-2026-06-19-190000 (deploy), BUG-2026-06-21-104800 (zombie), BUG-2026-07-15-120400 (zombie recurrence)

### Baseline

- **Python**: 167 tests pass (6.41s)
- **Web**: 89 tests pass (124ms)
- **G1**: PASS (23 bugs, 23 with tests)
- **G2**: PASS (6 phases identical)
- **G3**: PASS (scoring 93%, fixtures 98%, ranking 98%)
- **CI on main**: GREEN (last run 2026-07-30)
- **CI on PR #24**: RED (verify job — non-conventional merge commit)

---

## Audit Progress

### Phase 1: Parallel Module Audit — COMPLETE

| Agent     | Module             | Bugs Found                              |
| --------- | ------------------ | --------------------------------------- |
| general-1 | Bot Core           | 5 (1 high, 2 medium, 2 low)             |
| general-2 | Web Frontend       | 9 (1 critical, 1 high, 3 medium, 4 low) |
| general-3 | Scoring & Fixtures | 8 (2 high, 2 medium, 4 low)             |
| general-4 | Infrastructure     | 11 (2 P1, 5 P2, 4 P3)                   |
| **Total** |                    | **33**                                  |

### Phase 2: Bug Fixes — IN PROGRESS

### Phase 3: Verification — PENDING

---

## New Bugs Found (33 total)

### CRITICAL — Security

| #   | Module | File            | Bug                                                            | Severity |
| --- | ------ | --------------- | -------------------------------------------------------------- | -------- |
| 1   | Web    | transport.js:11 | Hardcoded BigBase service-account credentials in client bundle | CRITICAL |

### HIGH — Data Correctness / UX

| #   | Module         | File                            | Bug                                                                                                      | Severity |
| --- | -------------- | ------------------------------- | -------------------------------------------------------------------------------------------------------- | -------- |
| 2   | Scoring        | group_publisher.py:31           | `format_resultado` hardcodes `== 3` for cravadores — knockout exact matches never announced              | HIGH     |
| 3   | Scoring        | ranking.py:56 vs scoring.js:202 | Ranking sort order diverges — Python uses 4 tiebreakers, JS uses 3 (missing `acertos`)                   | HIGH     |
| 4   | Web            | style.css:176-178               | Bottom nav CSS `display: flex` overrides `display: none` — visible on all screen sizes until media query | HIGH     |
| 5   | Infrastructure | bigbase.py:80-89                | `list_records` silently truncates at 1000 records — palpites collection can exceed this                  | P1       |
| 6   | Infrastructure | app.py:57-60                    | Telegram token prefix logged in structured JSON output                                                   | P1       |

### MEDIUM — Reliability / Correctness

| #   | Module         | File                | Bug                                                                                | Severity |
| --- | -------------- | ------------------- | ---------------------------------------------------------------------------------- | -------- |
| 7   | Web            | store.js:27         | `loadAll()` sets `loaded=true` on failure — permanent lockout, no retry            | MEDIUM   |
| 8   | Bot            | handlers.py:176-208 | `cb_escolher_jogo` and `cb_gols_casa` lack try/except (unlike `cb_gols_fora`)      | MEDIUM   |
| 9   | Scoring        | fixtures.py:197-211 | `normalise()` assigns status `"encerrado"` even when `parse_result()` returns None | MEDIUM   |
| 10  | Scoring        | scoring.js:159-206  | JS ranking missing `jogos` field — parity violation with Python                    | MEDIUM   |
| 11  | Web            | transport.js:6-14   | Token cached forever — no refresh on 401 expiry                                    | MEDIUM   |
| 12  | Web            | JogosView.vue:23-31 | `savePalpite` has no error handling — modal gets stuck on API failure              | MEDIUM   |
| 13  | Infrastructure | bigbase.py:58-65    | Token refresh race condition under concurrent async requests                       | P2       |
| 14  | Infrastructure | app.py:70-73        | Missing `drop_pending_updates=True` in `run_polling()` (deploy entrypoint)         | P2       |
| 15  | Infrastructure | ci-cd.yml:158-166   | CI verify fails on merge commits — regex doesn't skip `Merge` commits              | P2       |
| 16  | Infrastructure | ci-cd.yml:272-286   | CI deploy doesn't wait for web-build-commit — serves stale dist on release         | P2       |
| 17  | Infrastructure | app.py:51-54        | Manual `asyncio.new_event_loop()` conflicts with PTB 22.x (owns its own loop)      | P2       |

### LOW — Code Quality / Edge Cases

| #   | Module         | File                           | Bug                                                                             | Severity |
| --- | -------------- | ------------------------------ | ------------------------------------------------------------------------------- | -------- |
| 18  | Bot            | handlers.py:355-367            | `_sync_resultados` counts `novos` without checking `set_resultado` return value | LOW      |
| 19  | Bot            | betting_flow.py:106-110        | `BettingFlow.validate_transition()` is dead code (defined+tested, never called) | LOW      |
| 20  | Bot            | handlers.py/bot.py             | `pending_results` queue in-memory only — lost on bot restart                    | LOW      |
| 21  | Scoring        | ranking.py:7 vs scoring.js:161 | `_VALID_TG_MIN=0` includes ID 0 (Python `>=0`); JS uses `>0`                    | LOW      |
| 22  | Scoring        | scoring.py:122                 | `parse_result` warning uses truthiness instead of `is not None` for numeric 0   | LOW      |
| 23  | Web            | style.css:202-270              | Triple-duplicated `.app-footer` and `.footer-content` CSS rules                 | LOW      |
| 24  | Infrastructure | app.py:140-148                 | `log_message` status `isdigit()` can raise `AttributeError` on non-string       | P3       |
| 25  | Infrastructure | config.py:14,19-20             | Bare `KeyError` on missing env vars (no actionable error message)               | P3       |
| 26  | Infrastructure | scripts/redeploy.py:6-10       | No error handling for login failure                                             | P3       |
| 27  | Infrastructure | results.py:97-98               | New `httpx.AsyncClient` per call (perf: new TCP+TLS each time)                  | P3       |

---

## Existing Open Bugs

| bug_id                | date       | severity | scope   | summary                                           | status | issue |
| --------------------- | ---------- | -------- | ------- | ------------------------------------------------- | ------ | ----- |
| BUG-2026-06-19-190000 | 2026-06-19 | medium   | deploy  | BigBase root_path not propagated to DetectAppType | open   | —     |
| BUG-2026-06-21-104800 | 2026-06-21 | medium   | bot-ops | Zombie poller — stale bot instance                | open   | —     |
| BUG-2026-07-15-120400 | 2026-07-15 | high     | bot-ops | Zombie poller recurrence — 409 Conflict           | open   | —     |

---

## Fixes Applied

(Updated as fixes land)

| bug_id | date | files_changed | approach | tests_added | status |
| ------ | ---- | ------------- | -------- | ----------- | ------ |
