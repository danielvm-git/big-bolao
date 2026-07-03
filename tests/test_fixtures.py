"""Tests for bolao/fixtures.py — phase parsing, time conversion, normalise()."""
import pytest
from bolao.fixtures import _parse_phase, _to_brt_iso, normalise, parse_result


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

    def test_finished_match_uses_et_score(self):
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


# ── parse_result — status-aware field selection ──────────────────────────────

class TestParseResultFieldSelection:
    """parse_result() defaults to ft_score (safe); only ET statuses use match_score."""

    # ── ET matches: use match_*_score (ET goals count) ─────────────────────

    @pytest.mark.parametrize("status", ["After ET", "AET", "Finished AET"])
    def test_et_statuses_use_match_score(self, status):
        """ET goals count — match_*_score must be preferred for ET statuses."""
        fx = {
            "match_status": status,
            "match_hometeam_score": "2", "match_awayteam_score": "1",
            "match_hometeam_ft_score": "1", "match_awayteam_ft_score": "1",
        }
        assert parse_result(fx) == (2, 1)

    # ── Everyone else defaults to ft_score (safe) ──────────────────────────

    @pytest.mark.parametrize("status", [
        "After Pen.", "PEN", "Finished PEN",  # penalty variants
        "Finished", "FT",                       # regular finish
        "Half Time", "Not Started",             # not finished (shouldn't happen but safe)
        "Some New Status",                      # unknown future status
    ])
    def test_non_et_statuses_use_ft_score(self, status):
        """Any status NOT explicitly ET defaults to ft_score (safe).

        This defends against API status-string drift — if the API adds a new
        penalty status we haven't seen before, we still read the reliable
        ft_score field instead of the potentially-inflated match_score.
        """
        fx = {
            "match_status": status,
            "match_hometeam_score": "99", "match_awayteam_score": "99",
            "match_hometeam_ft_score": "1", "match_awayteam_ft_score": "1",
        }
        assert parse_result(fx) == (1, 1)

    def test_non_et_falls_back_to_match_score_when_ft_missing(self):
        """When ft_score is absent, fall back to match_score (graceful degradation)."""
        fx = {
            "match_status": "Finished",
            "match_hometeam_score": "3", "match_awayteam_score": "0",
            "match_hometeam_ft_score": "", "match_awayteam_ft_score": "",
        }
        assert parse_result(fx) == (3, 0)
