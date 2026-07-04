# Traceability Matrix — Bugs → Tests

Each known bug is listed with its guarding test(s). **GAP** marks bugs with no
test coverage. Planned coverage (via epic e06 stories) is noted.

## Bug-to-test mapping

| Bug                                                       | Module           | Guarding test(s)                                                    | Coverage                               |
| --------------------------------------------------------- | ---------------- | ------------------------------------------------------------------- | -------------------------------------- |
| BUG-2026-06-19-180800-sync-misconfiguration               | config           | `test_config.py::TestStartupGuards`                                 | ✅ Partial (config guards only)        |
| BUG-2026-06-19-183500-nav-buttons                         | web/UI           | None                                                                | ❌ **GAP**                             |
| BUG-2026-06-19-190000-deploy-fail                         | deploy           | CI/CD workflow                                                      | ✅ Workflow-level                      |
| BUG-2026-06-19-215300-dashboard-zero-jogos                | web/UI           | None                                                                | ❌ **GAP**                             |
| BUG-2026-06-20-100000-duplicate-participants              | bigbase          | `test_participantes.py` (6 tests)                                   | ✅ Covered                             |
| BUG-2026-06-20-143237-missing-country-flags               | web/flags        | `web/tests/flags.test.js`                                           | ✅ Covered                             |
| BUG-2026-06-20-173500-instant-view-ogimage-svg            | web/landing      | None                                                                | ❌ **GAP** (design-only)               |
| BUG-2026-06-20-190000-bosnia-ampersand-flag               | web/flags        | `web/tests/flags.test.js`                                           | ✅ Covered                             |
| BUG-2026-06-20-200000-handlers-god-module                 | handlers         | None (architectural)                                                | ❌ **GAP** (refactor needed)           |
| BUG-2026-06-20-200100-api-js-six-responsibilities         | web/api.js       | `web/tests/*.test.js`                                               | ✅ Covered by transport/queries tests  |
| BUG-2026-06-20-200200-results-fixtures-duplicated-parsing | fixtures/results | `test_fixtures.py`, `test_results.py`                               | ✅ Covered                             |
| BUG-2026-06-20-200300-bigbase-dead-interface-surface      | bigbase          | `test_participantes.py`                                             | ⚠️ Partial (participant-only)          |
| BUG-2026-06-21-104800-stale-ranking-zombie-poller         | bot/poller       | `test_bot.py` (5 tests: conflict, drop_pending, allowed_updates)    | ✅ Covered                             |
| BUG-2026-06-21-124200-ranking-format-regression           | ranking          | `test_ranking.py::test_formatar_*`                                  | ✅ Covered                             |
| BUG-2026-06-28-003000-logger-not-committed                | repo             | `test_logger.py`                                                    | ✅ Covered                             |
| BUG-2026-06-30-140000-wrong-score-after-pen               | fixtures         | `test_fixtures.py::TestParseResultFieldSelection` (golden fixture)  | ✅ Covered                             |
| BUG-2026-06-30-150000-web-scoring-not-phase-aware         | scoring          | `tests/test_scoring.py` + `web/tests/scoring-golden.test.js`       | ✅ Covered (shared golden fixture)     |
| BUG-2026-07-03-191600-wrong-score-after-pen-recurrence    | fixtures         | `test_fixtures.py::TestParseResultFieldSelection` (golden fixture)  | ✅ Covered                             |
| BUG-2026-07-04-170000-knockout-exact-bets-mislabeled      | scoring          | `web/tests/scoring-golden.test.js` (scoreLabelFor assertions)       | ✅ Covered                             |

**Summary:** 19 bugs tracked — ✅ 15 covered, ⚠️ 1 partial, ❌ 3 GAP

## GAP analysis

| GAP | Bug/Area                      | Planned fix                         |
| --- | ----------------------------- | ----------------------------------- |
| 1   | nav-buttons (web UI)          | Accept — manual UI testing          |
| 2   | dashboard-zero-jogos (web UI) | Accept — edge case                  |
| 3   | instant-view-ogimage-svg      | Accept — design file                |
| 4   | handlers-god-module           | Architectural refactor (future)     |

## Requirement/story traceability

| Story                    | Guarding test(s)                                                          | Status                        |
| ------------------------ | ------------------------------------------------------------------------- | ----------------------------- |
| e01: Mobile SPA          | `web/tests/*.test.js` (35 tests)                                          | ✅ Done                       |
| e02: API integration     | `tests/test_fixtures.py`, `tests/test_results.py`, `tests/test_config.py` | ⚠️ Partial (2/6 stories done) |
| e03: Web Dashboard       | `web/tests/scoring.test.js`, `web/tests/flags.test.js`                    | ✅ Done                       |
| e04: CI/CD               | `.github/workflows/ci-cd.yml` (workflow-level)                            | ✅ Done                       |
| e05: Quiet Hours         | `tests/test_quiet_hours.py` (16 tests)                                    | ✅ Done                       |
| e06-s01: Test foundation | (this document)                                                           | ✅ Done                       |
| e06-s02: Golden fixture  | `tests/test_scoring.py`, `web/tests/scoring-golden.test.js`               | ✅ Done                       |
| e06-s03: Bug fix         | `web/tests/scoring-golden.test.js` (scoreLabelFor assertions)             | ✅ Done                       |
| e06-s04: Parse golden    | `test_fixtures.py::TestParseResultFieldSelection` (golden-fixture sourced) | 🔄 In progress                |
| e06-s05: Governance      | `scripts/check_test_governance.py`, `scripts/check_scoring_tables.py`     | 📅 Planned                    |
| e06-s06: Docs            | Updated CLAUDE.md                                                         | 📅 Planned                    |

## Coverage targets (P0 modules)

| Module               | Current              | Target | Gate                   |
| -------------------- | -------------------- | ------ | ---------------------- |
| `bolao/scoring`      | ~85%                 | 90%    | e06-s05 coverage gate  |
| `bolao/fixtures`     | ~90%                 | 90%    | ✅ Met                  |
| `bolao/ranking`      | ~80%                 | 90%    | e06-s05 coverage gate  |
| `web/src/scoring.js` | ~75%                 | 85%    | e06-s05 (manual check) |
