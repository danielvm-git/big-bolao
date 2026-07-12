#!/usr/bin/env bash
set -euo pipefail

# Preflight: run before merging to main.
# This script is called by the CI/CD verify job.

echo "=== Preflight: Python tests ==="
python -m pytest tests/ -v

echo "=== Preflight: Governance G1 (bug registry) ==="
python3 scripts/check_test_governance.py

echo "=== Preflight: Governance G2 (scoring parity) ==="
python3 scripts/check_scoring_tables.py

echo "=== Preflight: Governance G3 (P0 coverage) ==="
python -m pytest --cov=bolao.scoring --cov-fail-under=90 tests/test_scoring.py -q
python -m pytest --cov=bolao.fixtures --cov-fail-under=90 tests/test_fixtures.py -q
python -m pytest --cov=bolao.ranking --cov-fail-under=90 tests/test_ranking.py -q

echo "=== Preflight: Web tests ==="
cd web && node --test tests/*.test.js

echo "=== Preflight PASSED ==="
