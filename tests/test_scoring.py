"""Integration test: Python scoring matches the shared golden fixture.

Loads specs/test-strategy/scoring-golden.json, iterates every case,
calls bolao.scoring.pontos() with the case params, and asserts the
result matches expected_pontos. This is the Python half of the
Python↔JS parity invariant enforced by e06-s02.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from bolao.scoring import pontos

GOLDEN = Path(__file__).resolve().parent.parent / "specs" / "test-strategy" / "scoring-golden.json"


def _load_cases() -> list[dict]:
    with open(GOLDEN) as f:
        return json.load(f)


def test_golden_fixture_exists() -> None:
    assert GOLDEN.exists(), f"Golden fixture not found: {GOLDEN}"
    cases = _load_cases()
    assert len(cases) >= 21, f"Expected ≥21 cases, got {len(cases)}"


@pytest.mark.parametrize(
    "desc,pa,pb,ra,rb,match_id,expected",
    [
        (c["desc"], c["pa"], c["pb"], c["ra"], c["rb"], c["match_id"], c["expected"])
        for c in _load_cases()
    ],
)
def test_scoring_parity(desc: str, pa: int, pb: int, ra: int, rb: int, match_id: str, expected: int) -> None:
    result = pontos(pa, pb, ra, rb, match_id)
    assert result == expected, f"[{desc}] pontos({pa},{pb},{ra},{rb},{match_id!r}) = {result}, expected {expected}"
