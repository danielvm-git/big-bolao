"""Tests for bolao/fixtures.py — phase parsing, time conversion, normalise()."""
import pytest
from bolao.fixtures import _parse_phase, _to_brt_iso, normalise, parse_result, fetch_from_api


# ── _parse_phase ────────────────────────────────────────────────────────────

class TestParsePhase:
    def test_numeric_group_rounds(self):
        assert _parse_phase("1") == ("R1", 1)
        assert _parse_phase("2") == ("R2", 2)
        assert _parse_phase("3") == ("R3", 3)

    def test_numeric_knockout_rounds(self):
        assert _parse_phase("4") == ("R32", 4)
        assert _parse_phase("5") == ("R16", 5)
        assert _parse_phase("6") == ("QF",  6)
        assert _parse_phase("7") == ("SF",  7)
        assert _parse_phase("8") == ("3P",  8)
        assert _parse_phase("9") == ("FIN", 9)

    def test_string_group_rounds(self):
        assert _parse_phase("Group Stage - 1") == ("R1", 1)
        assert _parse_phase("Group Stage - 2") == ("R2", 2)
        assert _parse_phase("Group Stage - 3") == ("R3", 3)

    def test_string_knockout_rounds(self):
        assert _parse_phase("Round of 32")    == ("R32", 4)
        assert _parse_phase("Round of 16")    == ("R16", 5)
        assert _parse_phase("Quarter-finals") == ("QF",  6)
        assert _parse_phase("Semi-finals")    == ("SF",  7)
        assert _parse_phase("3rd Place Final") == ("3P", 8)
        assert _parse_phase("Final")          == ("FIN", 9)

    def test_unknown_returns_none(self):
        assert _parse_phase("Friendly") is None
        assert _parse_phase("") is None
        assert _parse_phase("Qualifier") is None


# ── _to_brt_iso ─────────────────────────────────────────────────────────────

class TestToBrtIso:
    def test_basic(self):
        assert _to_brt_iso("2026-06-11", "16:00") == "2026-06-11T16:00:00"

    def test_strips_extra_seconds(self):
        assert _to_brt_iso("2026-06-11", "16:00:00") == "2026-06-11T16:00:00"

    def test_midnight(self):
        assert _to_brt_iso("2026-06-12", "00:00") == "2026-06-12T00:00:00"


# ── normalise() ─────────────────────────────────────────────────────────────

_MOCK = [
    {
        "match_id": "9001", "match_round": "1",
        "match_date": "2026-06-11", "match_time": "16:00",
        "match_hometeam_name": "Mexico", "match_awayteam_name": "South Africa",
        "match_hometeam_score": "", "match_awayteam_score": "",
        "match_hometeam_ft_score": "", "match_awayteam_ft_score": "",
        "match_status": "Not Started",
    },
    {
        "match_id": "9002", "match_round": "4",
        "match_date": "2026-07-02", "match_time": "20:00",
        "match_hometeam_name": "Brazil", "match_awayteam_name": "Germany",
        "match_hometeam_score": "2", "match_awayteam_score": "1",
        "match_hometeam_ft_score": "2", "match_awayteam_ft_score": "1",
        "match_status": "Finished",
    },
    {
        "match_id": "9003", "match_round": "Friendly",  # ignored
        "match_date": "2026-05-01", "match_time": "19:00",
        "match_hometeam_name": "X", "match_awayteam_name": "Y",
        "match_hometeam_score": "", "match_awayteam_score": "",
        "match_hometeam_ft_score": "", "match_awayteam_ft_score": "",
        "match_status": "Not Started",
    },
]


class TestNormalise:
    def test_filters_unknown_phases(self):
        result = normalise(_MOCK)
        assert len(result) == 2

    def test_pending_match(self):
        result = normalise(_MOCK)
        m = next(r for r in result if r["api_fixture_id"] == "9001")
        assert m["match_id"] == "R1-01"
        assert m["kickoff"] == "2026-06-11T16:00:00"
        assert m["casa"] == "Mexico"
        assert m["fora"] == "South Africa"
        assert m["status"] == "agendado"
        assert m["gols_casa"] is None
        assert m["gols_fora"] is None

    def test_finished_match_extracts_score(self):
        result = normalise(_MOCK)
        m = next(r for r in result if r["api_fixture_id"] == "9002")
        assert m["match_id"] == "R32-01"
        assert m["status"] == "encerrado"
        assert m["gols_casa"] == 2
        assert m["gols_fora"] == 1

    def test_et_score_fallback_to_ft(self):
        """When match_*_score absent, falls back to ft_score (90 min)."""
        fx = {**_MOCK[1], "match_hometeam_score": "", "match_awayteam_score": ""}
        result = normalise([fx])
        assert result[0]["gols_casa"] == 2

    def test_no_internal_fields_leaked(self):
        result = normalise(_MOCK)
        for r in result:
            assert "_phase_id" not in r
            assert "_kickoff_sort" not in r

    def test_sorted_by_kickoff(self):
        result = normalise(_MOCK)
        kickoffs = [r["kickoff"] for r in result]
        assert kickoffs == sorted(kickoffs)


# ── parse_result — golden fixture tests ────────────────────────────────────
#
# DESIGN DECISION: we use a DENYLIST-like approach — only ET statuses get
# match_score; everything else gets ft_score. This defends against API
# status-string drift. If apifootball adds a new penalty status we haven't
# seen, we still read ft_score (correct) instead of match_score (unreliable
# for penalty-decided matches). See BUG-2026-06-30-140000 and its recurrence.
#
# The golden fixture (specs/test-strategy/parse-result-golden.json) is the
# single source of truth for all parse_result() code paths. Add new cases
# there, not here. Tests/ directory mirrors this invariant.

import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_GOLDEN = _HERE.parent / "specs" / "test-strategy" / "parse-result-golden.json"
with open(_GOLDEN) as _f:
    _PARSE_CASES = json.load(_f)


class TestParseResultFieldSelection:
    """parse_result() defaults to ft_score (safe); only ET statuses use match_score."""

    def test_golden_has_at_least_15_cases(self):
        assert len(_PARSE_CASES) >= 15, f"Expected ≥15 cases, got {len(_PARSE_CASES)}"

    @pytest.mark.parametrize("c", _PARSE_CASES, ids=lambda c: c["desc"])
    def test_parse_result_golden(self, c):
        """Every golden case must match parse_result()."""
        fx = {
            "match_status": c["match_status"],
            "match_hometeam_score": c["match_hometeam_score"],
            "match_awayteam_score": c["match_awayteam_score"],
            "match_hometeam_ft_score": c["match_hometeam_ft_score"],
            "match_awayteam_ft_score": c["match_awayteam_ft_score"],
        }
        result = parse_result(fx)
        expected = (
            (c["expected_home"], c["expected_away"])
            if c["expected_home"] is not None
            else None
        )
        assert result == expected, (
            f"parse_result({c['desc']!r}): "
            f"got {result}, expected {expected}"
        )


# ── fetch_from_api (mocked HTTP) ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_from_api_returns_normalised_fixtures():
    """fetch_from_api() must call the API and return normalised fixtures."""
    from unittest.mock import patch

    class MockResponse:
        def raise_for_status(self):
            pass
        def json(self):
            return [{
                "match_id": "12345",
                "match_round": "4",
                "match_date": "2026-07-02",
                "match_time": "20:00",
                "match_hometeam_name": "Brazil",
                "match_awayteam_name": "Germany",
                "match_hometeam_score": "2",
                "match_awayteam_score": "1",
                "match_hometeam_ft_score": "2",
                "match_awayteam_ft_score": "1",
                "match_status": "Finished",
            }]

    mock_response = MockResponse()

    with patch("bolao.fixtures.config.APIFOOTBALL_KEY", "test-key-123"):
        with patch("bolao.fixtures.config.APIFOOTBALL_LEAGUE_ID", "28"):
            with patch("bolao.fixtures.httpx.AsyncClient") as MockClient:
                instance = MockClient.return_value.__aenter__.return_value
                instance.get.return_value = mock_response
                result = await fetch_from_api()

    assert len(result) == 1
    assert result[0]["casa"] == "Brazil"
    assert result[0]["fora"] == "Germany"
    assert result[0]["match_id"] == "R32-01"
    assert result[0]["status"] == "encerrado"


# ── _parse_phase date inference edge case ──────────────────────────────────

def test_parse_phase_date_fallback():
    """Phase must be inferred from date when round_str is empty."""
    # R16 range is 2026-07-04 to 2026-07-08
    phase = _parse_phase("", "2026-07-04")
    assert phase == ("R16", 5), f"Expected R16/5, got {phase}"

    # QF range is 2026-07-09 to 2026-07-12
    phase = _parse_phase("", "2026-07-10")
    assert phase == ("QF", 6), f"Expected QF/6, got {phase}"

    # Outside all ranges should return None
    phase = _parse_phase("", "2026-05-01")
    assert phase is None, f"Expected None, got {phase}"
