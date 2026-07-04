# Quality Gate — Definition-of-Done & Gate Rubric

## Overview

Every release to `main` must pass three governance gates before deploy. These
gates are enforced in CI/CD (`.github/workflows/ci-cd.yml`) and must also pass
locally before merging a feature branch.

## The Three Gates

### Gate 1: Bug Registry

**Script:** `scripts/check_test_governance.py`

Every `specs/bugs/BUG-*.md` file MUST have a corresponding entry in
`specs/bugs/registry.yaml` with:
- `bug_id` matching the file prefix (BUG-YYYY-MM-DD-NNNNNN)
- `tests_added` field listing guarding tests (empty list `[]` is OK — means
  "explicitly decided no tests")

**Failure:** Build fails. Fix by adding the missing registry entry.

### Gate 2: Scoring Table Parity

**Script:** `scripts/check_scoring_tables.py`

`FASE_PONTOS` in `bolao/scoring.py` and `web/src/scoring.js` MUST be identical
for every phase. If a new phase or scoring value is added in one language, it
must be mirrored in the other.

**Failure:** Build fails. Fix by updating the lagging table.

### Gate 3: P0 Coverage

Each P0 module runs its own coverage check with `--cov-fail-under=90`:

```bash
python -m pytest --cov=bolao.scoring   --cov-fail-under=90 tests/test_scoring.py -q
python -m pytest --cov=bolao.fixtures  --cov-fail-under=90 tests/test_fixtures.py -q
python -m pytest --cov=bolao.ranking   --cov-fail-under=90 tests/test_ranking.py -q
```

| Module            | Current | Target | Status |
| ----------------- | ------- | ------ | ------ |
| `bolao/scoring`   | 100%    | 90%    | ✅     |
| `bolao/fixtures`  | 81%     | 90%    | 🟡 Gap — needs fixture tests |
| `bolao/ranking`   | 98%     | 90%    | ✅     |

**Failure:** Build fails. Fix by adding tests for the uncovered lines in the
failing module. Run the specific module's test file to see missing lines.

## CI/CD Pipeline Gate Positions

```
semantic-release → web build → Python tests → GOVERNANCE GATES → web tests → deploy → health check
                                               ├── Gate 1: bug registry
                                               ├── Gate 2: scoring parity
                                               └── Gate 3: P0 coverage
```

All gates run only on new releases (after `detect-release` outputs
`new_release=true`).

## Adding a New Golden Fixture Case

1. Edit the appropriate golden JSON in `specs/test-strategy/`
   (`scoring-golden.json` or `parse-result-golden.json`).
2. The parametrized test in `tests/test_*.py` picks it up automatically.
3. For scoring: also add to `web/tests/scoring-golden.test.js`.
4. Run both Python and web suites to confirm.
5. If the golden fixture is parse-result, run `pytest tests/test_fixtures.py`.

## Registering a New Bug

1. Create `specs/bugs/BUG-YYYY-MM-DD-NNNNNN-description.md` with:
   - Title, description, root cause, fix approach
   - Status, tests_added section
2. Add entry to `specs/bugs/registry.yaml` with:
   - bug_id, date, severity, priority, scope, summary
   - file path, status, tests_added
3. Gate 1 will pass automatically.

## Local Pre-Merge Checklist

```bash
# Full test suite
python -m pytest tests/ -q

# Web tests
cd web && node --test tests/*.test.js

# Governance gates
python3 scripts/check_test_governance.py
python3 scripts/check_scoring_tables.py

# P0 coverage (per module)
python -m pytest --cov=bolao.scoring  --cov-fail-under=90 tests/test_scoring.py -q
python -m pytest --cov=bolao.fixtures --cov-fail-under=90 tests/test_fixtures.py -q
python -m pytest --cov=bolao.ranking  --cov-fail-under=90 tests/test_ranking.py -q
```
