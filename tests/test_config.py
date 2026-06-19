"""Tests for bolao/config.py — startup guards catch misconfiguration."""
import pytest
from bolao.config import validate_config


class TestStartupGuards:
    def test_apifootball_without_key_raises(self):
        with pytest.raises(RuntimeError, match="APIFOOTBALL_KEY"):
            validate_config(provider="apifootball", key="", league_id="28")

    def test_apifootball_without_league_id_raises(self):
        with pytest.raises(RuntimeError, match="APIFOOTBALL_LEAGUE_ID"):
            validate_config(provider="apifootball", key="somekey", league_id="")

    def test_apifootball_with_league_id_1_warns(self):
        with pytest.warns(UserWarning, match="valor padrao antigo"):
            validate_config(provider="apifootball", key="somekey", league_id="1")

    def test_manual_mode_no_guard_needed(self):
        """Empty provider (manual mode) should not raise or warn."""
        validate_config(provider="", key="", league_id="")  # no exception

    def test_correct_config_loads_fine(self):
        validate_config(provider="apifootball", key="somekey", league_id="28")
