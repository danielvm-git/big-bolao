"""Tests for bolao.betting_flow — callback data state machine."""
from __future__ import annotations

import pytest
from bolao.betting_flow import BettingFlow, Step


class TestSerialize:
    """BettingFlow.serialize produces correct callback_data strings."""

    def test_escolher_jogo(self):
        data = BettingFlow.serialize(Step.ESCOLHER_JOGO, match_id="R1-01")
        assert data == "g|R1-01"

    def test_escolher_jogo_complex_id(self):
        data = BettingFlow.serialize(Step.ESCOLHER_JOGO, match_id="SF-02")
        assert data == "g|SF-02"

    def test_gols_casa(self):
        data = BettingFlow.serialize(Step.GOLS_CASA, match_id="R1-01", gols=3)
        assert data == "h|R1-01|3"

    def test_gols_casa_zero(self):
        data = BettingFlow.serialize(Step.GOLS_CASA, match_id="R1-01", gols=0)
        assert data == "h|R1-01|0"

    def test_gols_fora(self):
        data = BettingFlow.serialize(Step.GOLS_FORA, match_id="R1-01", gc=2, gf=1)
        assert data == "f|R1-01|2|1"

    def test_gols_fora_zero_both(self):
        data = BettingFlow.serialize(Step.GOLS_FORA, match_id="R1-01", gc=0, gf=0)
        assert data == "f|R1-01|0|0"

    def test_gols_fora_large(self):
        data = BettingFlow.serialize(Step.GOLS_FORA, match_id="G-99", gc=7, gf=6)
        assert data == "f|G-99|7|6"


class TestDeserialize:
    """BettingFlow.deserialize parses callback_data back to (Step, params)."""

    def test_escolher_jogo(self):
        step, params = BettingFlow.deserialize("g|R1-01")
        assert step == Step.ESCOLHER_JOGO
        assert params == {"match_id": "R1-01"}

    def test_gols_casa_int_conversion(self):
        step, params = BettingFlow.deserialize("h|R1-01|3")
        assert step == Step.GOLS_CASA
        assert params == {"match_id": "R1-01", "gols": 3}
        assert isinstance(params["gols"], int)

    def test_gols_casa_zero(self):
        step, params = BettingFlow.deserialize("h|R1-01|0")
        assert step == Step.GOLS_CASA
        assert params == {"match_id": "R1-01", "gols": 0}

    def test_gols_fora_int_conversion(self):
        step, params = BettingFlow.deserialize("f|R1-01|2|1")
        assert step == Step.GOLS_FORA
        assert params == {"match_id": "R1-01", "gc": 2, "gf": 1}
        assert isinstance(params["gc"], int)
        assert isinstance(params["gf"], int)

    def test_gols_fora_large(self):
        step, params = BettingFlow.deserialize("f|G-99|7|6")
        assert step == Step.GOLS_FORA
        assert params == {"match_id": "G-99", "gc": 7, "gf": 6}


class TestRoundTrip:
    """serialize → deserialize round-trips preserve all data."""

    def test_escolher_jogo_round_trip(self):
        data = BettingFlow.serialize(Step.ESCOLHER_JOGO, match_id="QF-04")
        step, params = BettingFlow.deserialize(data)
        assert step == Step.ESCOLHER_JOGO
        assert params["match_id"] == "QF-04"

    def test_gols_casa_round_trip(self):
        data = BettingFlow.serialize(Step.GOLS_CASA, match_id="R1-02", gols=5)
        step, params = BettingFlow.deserialize(data)
        assert step == Step.GOLS_CASA
        assert params["match_id"] == "R1-02"
        assert params["gols"] == 5

    def test_gols_fora_round_trip(self):
        data = BettingFlow.serialize(Step.GOLS_FORA, match_id="R1-02", gc=3, gf=2)
        step, params = BettingFlow.deserialize(data)
        assert step == Step.GOLS_FORA
        assert params["match_id"] == "R1-02"
        assert params["gc"] == 3
        assert params["gf"] == 2


class TestInvalidInputs:
    """BettingFlow.deserialize returns None for malformed input."""

    def test_empty_string(self):
        assert BettingFlow.deserialize("") is None

    def test_illegal_prefix(self):
        assert BettingFlow.deserialize("z|R1-01") is None

    def test_only_prefix(self):
        assert BettingFlow.deserialize("g") is None

    def test_gols_casa_missing_gols(self):
        assert BettingFlow.deserialize("h|R1-01") is None

    def test_gols_casa_extra_fields(self):
        assert BettingFlow.deserialize("h|R1-01|2|3") is None

    def test_gols_fora_missing_fields(self):
        assert BettingFlow.deserialize("f|R1-01") is None

    def test_gols_fora_non_numeric_gc(self):
        assert BettingFlow.deserialize("f|R1-01|abc|1") is None

    def test_gols_fora_non_numeric_gf(self):
        assert BettingFlow.deserialize("f|R1-01|2|xyz") is None

    def test_none_value(self):
        assert BettingFlow.deserialize(None) is None

    def test_match_id_with_pipe_is_rejected(self):
        # callback_data is attacker-controllable; a match_id containing the "|"
        # delimiter must not mis-parse. match_ids are generated as R1-01/SF-02
        # (never contain "|"), so this locks in the boundary.
        assert BettingFlow.deserialize("g|R1|01") is None

    def test_gols_casa_with_pipe_is_rejected(self):
        assert BettingFlow.deserialize("h|R1|01|2") is None

    def test_gols_fora_with_pipe_is_rejected(self):
        assert BettingFlow.deserialize("f|R1|01|2|1") is None



class TestValidateTransition:
    """BettingFlow.validate_transition enforces correct step order."""

    def test_escolher_para_gols_casa(self):
        BettingFlow.validate_transition(Step.ESCOLHER_JOGO, Step.GOLS_CASA)

    def test_gols_casa_para_gols_fora(self):
        BettingFlow.validate_transition(Step.GOLS_CASA, Step.GOLS_FORA)

    def test_escolher_para_gols_fora_invalido(self):
        with pytest.raises(ValueError, match="invalid transition"):
            BettingFlow.validate_transition(Step.ESCOLHER_JOGO, Step.GOLS_FORA)

    def test_gols_fora_para_escolher_invalido(self):
        with pytest.raises(ValueError, match="invalid transition"):
            BettingFlow.validate_transition(Step.GOLS_FORA, Step.ESCOLHER_JOGO)

    def test_gols_casa_para_escolher_invalido(self):
        with pytest.raises(ValueError, match="invalid transition"):
            BettingFlow.validate_transition(Step.GOLS_CASA, Step.ESCOLHER_JOGO)

    def test_gols_fora_para_gols_casa_invalido(self):
        with pytest.raises(ValueError, match="invalid transition"):
            BettingFlow.validate_transition(Step.GOLS_FORA, Step.GOLS_CASA)


class TestPatternFor:
    """BettingFlow.pattern_for produces correct regex patterns."""

    def test_escolher_jogo_pattern(self):
        assert BettingFlow.pattern_for(Step.ESCOLHER_JOGO) == r"^g\|"

    def test_gols_casa_pattern(self):
        assert BettingFlow.pattern_for(Step.GOLS_CASA) == r"^h\|"

    def test_gols_fora_pattern(self):
        assert BettingFlow.pattern_for(Step.GOLS_FORA) == r"^f\|"
