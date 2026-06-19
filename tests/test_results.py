"""Tests for bolao/results.py — result matching by api_fixture_id and name fallback."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bolao.results import buscar_encerrados, _en


# ── _en helper ──────────────────────────────────────────────────────────────

class TestEnHelper:
    def test_known_pt_name(self):
        assert _en("Brasil") == "brazil"
        assert _en("França") == "france"

    def test_unknown_name_returned_lowercased(self):
        assert _en("Unknown Team") == "unknown team"


# ── helpers ─────────────────────────────────────────────────────────────────

def _mock_http(api_response: list):
    """Context manager that patches httpx.AsyncClient to return api_response."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value=api_response)

    mock_cli = AsyncMock()
    mock_cli.get = AsyncMock(return_value=mock_response)

    mock_client_cls = MagicMock()
    mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_cli)
    mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
    return patch("bolao.results.httpx.AsyncClient", mock_client_cls)


_API_RESPONSE = [
    {
        "match_id": "710281",
        "match_status": "Finished",
        "match_hometeam_name": "Mexico",
        "match_awayteam_name": "South Africa",
        "match_hometeam_ft_score": "2",
        "match_awayteam_ft_score": "0",
        "match_hometeam_score": "2",
        "match_awayteam_score": "0",
    },
    {
        "match_id": "710282",
        "match_status": "Not Started",
        "match_hometeam_name": "Brazil",
        "match_awayteam_name": "Haiti",
        "match_hometeam_ft_score": "",
        "match_awayteam_ft_score": "",
        "match_hometeam_score": "",
        "match_awayteam_score": "",
    },
]

_JOGOS = [
    {
        "match_id": "R1-01",
        "api_fixture_id": "710281",
        "casa": "Mexico", "fora": "South Africa",
        "status": "agendado",
    },
    {
        "match_id": "R2-07",
        "api_fixture_id": "710282",
        "casa": "Brazil", "fora": "Haiti",
        "status": "agendado",
    },
    {
        "match_id": "R1-06",
        "api_fixture_id": "999999",
        "casa": "Brasil", "fora": "Marrocos",
        "status": "encerrado",  # already done — must be skipped
    },
]


# ── buscar_encerrados ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_matches_by_api_fixture_id():
    """Finished games are matched exactly by api_fixture_id."""
    with patch("bolao.results.config.RESULTS_PROVIDER", "apifootball"), \
         patch("bolao.results.config.APIFOOTBALL_KEY", "fake-key"), \
         patch("bolao.results.config.APIFOOTBALL_LEAGUE_ID", "28"), \
         _mock_http(_API_RESPONSE):
        results = await buscar_encerrados(_JOGOS)

    assert len(results) == 1
    assert results[0].match_id == "R1-01"
    assert results[0].gols_casa == 2
    assert results[0].gols_fora == 0


@pytest.mark.asyncio
async def test_skips_already_encerrado():
    """Jogos with status=encerrado are never returned."""
    with patch("bolao.results.config.RESULTS_PROVIDER", "apifootball"), \
         patch("bolao.results.config.APIFOOTBALL_KEY", "fake-key"), \
         patch("bolao.results.config.APIFOOTBALL_LEAGUE_ID", "28"), \
         _mock_http(_API_RESPONSE):
        results = await buscar_encerrados(_JOGOS)

    match_ids = [r.match_id for r in results]
    assert "R1-06" not in match_ids


@pytest.mark.asyncio
async def test_returns_empty_when_no_provider():
    """Manual mode (no provider) always returns empty list."""
    with patch("bolao.results.config.RESULTS_PROVIDER", ""):
        results = await buscar_encerrados(_JOGOS)
    assert results == []


@pytest.mark.asyncio
async def test_uses_ft_score_not_total_score():
    """Scoring uses ft_score (90 min), ignoring ET score in match_*_score."""
    api_with_et = [{
        "match_id": "710281",
        "match_status": "After ET",
        "match_hometeam_name": "Mexico",
        "match_awayteam_name": "South Africa",
        "match_hometeam_ft_score": "1",   # 90-min score — must be used
        "match_awayteam_ft_score": "1",
        "match_hometeam_score": "2",       # ET score — must NOT be used
        "match_awayteam_score": "1",
    }]

    with patch("bolao.results.config.RESULTS_PROVIDER", "apifootball"), \
         patch("bolao.results.config.APIFOOTBALL_KEY", "fake-key"), \
         patch("bolao.results.config.APIFOOTBALL_LEAGUE_ID", "28"), \
         _mock_http(api_with_et):
        results = await buscar_encerrados([_JOGOS[0]])

    assert len(results) == 1
    assert results[0].gols_casa == 1   # ft_score, NOT 2 (ET total)
    assert results[0].gols_fora == 1


@pytest.mark.asyncio
async def test_name_fallback_when_no_api_fixture_id():
    """Falls back to PT→EN name matching for records without api_fixture_id."""
    jogo_sem_id = {
        "match_id": "R1-06",
        "api_fixture_id": "",          # no ID set
        "casa": "Brasil", "fora": "Marrocos",
        "status": "agendado",
    }
    api = [{
        "match_id": "99999",
        "match_status": "Finished",
        "match_hometeam_name": "Brazil",
        "match_awayteam_name": "Morocco",
        "match_hometeam_ft_score": "3",
        "match_awayteam_ft_score": "0",
        "match_hometeam_score": "3",
        "match_awayteam_score": "0",
    }]

    with patch("bolao.results.config.RESULTS_PROVIDER", "apifootball"), \
         patch("bolao.results.config.APIFOOTBALL_KEY", "fake-key"), \
         patch("bolao.results.config.APIFOOTBALL_LEAGUE_ID", "28"), \
         _mock_http(api):
        results = await buscar_encerrados([jogo_sem_id])

    assert len(results) == 1
    assert results[0].gols_casa == 3
