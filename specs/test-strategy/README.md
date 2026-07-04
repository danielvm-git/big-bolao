# Big Bolão — Test Strategy

## How to run every suite

### Python tests (pytest, 128 tests across 12 files)

```bash
# Full suite
python -m pytest tests/ -v

# Single file
python -m pytest tests/test_scoring.py -v

# Single test
python -m pytest tests/test_fixtures.py::TestParseResultFieldSelection -v

# Coverage for P0 modules (scoring, fixtures, ranking)
python -m pytest --cov=bolao/scoring --cov=bolao/fixtures --cov=bolao/ranking --cov-report=term-missing
```

**Setup:** `pip install -r requirements.txt` (includes pytest, pytest-asyncio).
Requires `.env` with at least `TELEGRAM_TOKEN`, `BIGBASE_EMAIL`, `BIGBASE_PASSWORD` for config tests.

### Web tests (node --test, 35 tests across 4 files)

```bash
cd web && node --test tests/*.test.js
```

**Setup:** `cd web && npm ci`. No build required for tests.

### CI suite (GitHub Actions)

`.github/workflows/ci-cd.yml` runs on push to `main`:

1. semantic-release (version bump)
2. Web build (`npm ci + vite build`)
3. Python tests (`pytest`)
4. BigBase deploy + health check

---

## Test file inventory

### Python (11 files, 128 tests)

| File                            | Tests | Covers                                                                                  | Notes                                                            |
| ------------------------------- | ----- | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `tests/test_betting_flow.py`    | 36    | `bolao/betting_flow.py` — state machine, serialize/deserialize, validation, transitions | Comprehensive coverage of step enum and conversation patterns    |
| `tests/test_bot.py`             | 5     | `bolao/bot.py` — polling config, error handler, `_post_init` startup                    | Requires async mocks; covers 409-conflict logging                |
| `tests/test_config.py`          | 5     | `bolao/config.py` — startup guards, env var validation                                  | Requires `.env` with test values                                 |
| `tests/test_fixtures.py`        | 20    | `bolao/fixtures.py` — `_parse_phase`, `_to_brt_iso`, `normalise`, `parse_result`        | Phase mapping, ET/penalty score selection, discrepancy detection |
| `tests/test_group_publisher.py` | 11    | `bolao/group_publisher.py` — result, ranking, lembrete formatting                       | Pure formatting, no I/O                                          |
| `tests/test_logger.py`          | 5     | `bolao/logger.py` — JSON formatter, module import                                       | Structural import checks                                         |
| `tests/test_participantes.py`   | 6     | `bolao/bigbase.py` — placeholder matching, reivindicar                                  | Substring matching with normalized names                         |
| `tests/test_quiet_hours.py`     | 16    | `bolao/util.py`, `bolao/handlers.py` — quiet hours gating, morning flush, manual bypass | Time-dependent; uses fixed-now mocking                           |
| `tests/test_ranking.py`         | 9     | `bolao/ranking.py` — calcular, formatar                                                 | Inactive exclusion, formatting                                   |
| `tests/test_results.py`         | 7     | `bolao/results.py` — API matching, ET score fallback                                    | Mocked API responses                                             |
| `tests/test_version.py`         | 3     | `bolao/version.py` — version check, `/version` handler                                  | Semver validation                                                |

**Missing Python test files (planned):**

- `tests/test_scoring.py` — golden fixture parity tests (planned e06-s02)

### Web (4 files, 35 tests)

| File                          | Tests     | Covers                                                         | Notes                           |
| ----------------------------- | --------- | -------------------------------------------------------------- | ------------------------------- |
| `web/tests/flags.test.js`     | flags     | `web/src/flags.js` — flag lookup by country name               | Team name matching              |
| `web/tests/queries.test.js`   | queries   | `web/src/queries.js` — API query functions                     | HTTP transport layer            |
| `web/tests/scoring.test.js`   | scoring   | `web/src/scoring.js` — `calcPontos`, `scoreLabel`, `flagEmoji` | Phase-aware scoring, formatting |
| `web/tests/transport.test.js` | transport | `web/src/transport.js` — HTTP client                           | BigBase API client              |

---

## Golden fixture files (planned, e06-s02 and e06-s04)

| File                                           | Purpose                                                                                | Consumed by                                                 |
| ---------------------------------------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `specs/test-strategy/scoring-golden.json`      | Scoring parity: Python `pontos()` == JS `calcPontos()` across all phases and bet types | `tests/test_scoring.py`, `web/tests/scoring-golden.test.js` |
| `specs/test-strategy/parse-result-golden.json` | Parse result: all ET/penalty status variants → expected score tuple                    | `tests/test_fixtures.py`                                    |

---

## Governance scripts (planned, e06-s05)

| Script                             | Purpose                                                                  |
| ---------------------------------- | ------------------------------------------------------------------------ |
| `scripts/check_test_governance.py` | Fails if any `specs/bugs/BUG-*.md` lacks registry entry or `tests_added` |
| `scripts/check_scoring_tables.py`  | Structural parity check: `FASE_PONTOS` in both Python and JS             |
