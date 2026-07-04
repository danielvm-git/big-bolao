"""Tests for bolao/bigbase.py — ensure_setup upsert from API.

Mock strategy: patch BigBase.list_records/.create/.patch with in-memory store;
patch bolao.fixtures.fetch_from_api to control API outcome.

Two test groups:
  1. API success path: fixtures are upserted with api_fixture_id as dedup key
  2. API failure/fallback path: RuntimeError → MATCHES hardcoded as before
"""
import pytest
from unittest.mock import AsyncMock, patch

from bolao.bigbase import BigBase, JOGOS


# ── helpers ──────────────────────────────────────────────────────────────


def _make_bb() -> BigBase:
    """Cria BigBase com list_records/create/patch mockados via store."""
    store: dict[str, list[dict]] = {
        "jogos": [],
        "participantes": [],
        "palpites": [],
    }

    bb = BigBase(url="http://test.local")
    bb._token = "fake-token"

    async def fake_list_records(collection: str, limit: int = 1000) -> list[dict]:
        return store.get(collection, [])

    async def fake_create(collection: str, data: dict) -> int:
        recs = store.setdefault(collection, [])
        new_id = max((r["id"] for r in recs), default=0) + 1
        store[collection].append({"id": new_id, **data})
        return new_id

    async def fake_patch(collection: str, rec_id: int, data: dict) -> None:
        for r in store.get(collection, []):
            if r["id"] == rec_id:
                r.update(data)
                return
        raise ValueError(f"record {rec_id} not found in {collection}")

    bb.list_records = AsyncMock(side_effect=fake_list_records)
    bb.create = AsyncMock(side_effect=fake_create)
    bb.patch = AsyncMock(side_effect=fake_patch)
    bb._store = store  # tests can inspect state
    return bb


def _api_fixture(
    match_id: str,
    api_fixture_id: str,
    casa: str = "Brasil",
    fora: str = "Argentina",
    kickoff: str = "2026-06-13T19:00:00",
    rodada: int = 1,
    gols_casa: int | None = None,
    gols_fora: int | None = None,
    status: str = "agendado",
) -> dict:
    return {
        "api_fixture_id": api_fixture_id,
        "match_id": match_id,
        "rodada": rodada,
        "kickoff": kickoff,
        "casa": casa,
        "fora": fora,
        "gols_casa": gols_casa,
        "gols_fora": gols_fora,
        "status": status,
    }


# ── help: verificar store ────────────────────────────────────────────────


def _jogos_no_store(bb: BigBase) -> list[dict]:
    return bb._store.get("jogos", [])


# ═════════════════════════════════════════════════════════════════════════
# Ciclo 1: API success — fresh seed (no existing jogos)
# ═════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_ensure_setup_api_success_creates_all():
    """Quando a API retorna fixtures e não há jogos existentes, cria todos."""
    bb = _make_bb()

    api_data = [
        _api_fixture("R1-01", "1001", "Brasil", "Argentina"),
        _api_fixture("R1-02", "1002", "Alemanha", "Japão"),
    ]

    with patch("bolao.bigbase.fetch_from_api", new=AsyncMock(return_value=api_data)):
        await bb.ensure_setup()

    jogos = _jogos_no_store(bb)
    assert len(jogos) == 2
    assert jogos[0]["match_id"] == "R1-01"
    assert jogos[0]["api_fixture_id"] == "1001"
    assert jogos[1]["match_id"] == "R1-02"
    assert jogos[1]["api_fixture_id"] == "1002"


# ═════════════════════════════════════════════════════════════════════════
# Ciclo 2: API success — partial existing (dedup by api_fixture_id)
# ═════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_ensure_setup_api_success_dedup_by_api_fixture_id():
    """Fixtures já existentes com api_fixture_id são atualizadas (patch),
    novas são criadas.
    """
    bb = _make_bb()
    # pre-popula store com um jogo existente
    bb._store["jogos"] = [
        {
            "id": 1,
            "api_fixture_id": "1001",
            "match_id": "R1-01",
            "casa": "Brasil",
            "fora": "Argentina",
            "gols_casa": None,
            "gols_fora": None,
            "status": "agendado",
        },
    ]

    api_data = [
        # mesma fixture — deve patch (atualizar dados)
        _api_fixture("R1-01", "1001", "Brasil", "Argentina",
                      gols_casa=2, gols_fora=1, status="encerrado"),
        # nova fixture — deve create
        _api_fixture("R1-02", "1002", "Alemanha", "Japão"),
    ]

    with patch("bolao.bigbase.fetch_from_api", new=AsyncMock(return_value=api_data)):
        await bb.ensure_setup()

    jogos = _jogos_no_store(bb)
    assert len(jogos) == 2

    # existente foi patchado com resultado
    j1 = next(j for j in jogos if j["api_fixture_id"] == "1001")
    assert j1["gols_casa"] == 2
    assert j1["gols_fora"] == 1
    assert j1["status"] == "encerrado"

    # nova foi criada
    j2 = next(j for j in jogos if j["api_fixture_id"] == "1002")
    assert j2["match_id"] == "R1-02"


# ═════════════════════════════════════════════════════════════════════════
# Ciclo 3: API success — existing by match_id migration
# ═════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_ensure_setup_api_success_migration_no_api_fixture_id():
    """Fixture existente sem api_fixture_id (criada pelo seed MATCHES original)
    é encontrada por match_id e recebe api_fixture_id via patch.
    """
    bb = _make_bb()
    bb._store["jogos"] = [
        {
            "id": 1,
            # sem api_fixture_id — como os registros criados pelo seed original
            "match_id": "R1-01",
            "casa": "Brasil",
            "fora": "Argentina",
            "gols_casa": None,
            "gols_fora": None,
            "status": "agendado",
            "rodada": 1,
            "kickoff": "2026-06-13T19:00:00",
        },
    ]

    api_data = [
        _api_fixture("R1-01", "1001", "Brasil", "Argentina"),
    ]

    with patch("bolao.bigbase.fetch_from_api", new=AsyncMock(return_value=api_data)):
        await bb.ensure_setup()

    jogos = _jogos_no_store(bb)
    assert len(jogos) == 1  # não criou duplicata
    assert jogos[0]["api_fixture_id"] == "1001"
    assert jogos[0]["id"] == 1  # mesmo registro, não duplicou


# ═════════════════════════════════════════════════════════════════════════
# Ciclo 4: API failure — fallback to MATCHES
# ═════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_ensure_setup_api_failure_fallback_matches():
    """Quando fetch_from_api levanta RuntimeError, ensure_setup usa MATCHES
    hardcoded (comportamento atual).
    """
    bb = _make_bb()

    with patch("bolao.bigbase.fetch_from_api",
               new=AsyncMock(side_effect=RuntimeError("API offline"))):
        await bb.ensure_setup()

    jogos = _jogos_no_store(bb)
    # MATCHES tem 72 jogos
    assert len(jogos) == 72
    # Verifica alguns jogos conhecidos
    match_ids = {j["match_id"] for j in jogos}
    assert "R1-01" in match_ids
    assert "R3-24" in match_ids  # último jogo
    # Nenhum fixture da API tem api_fixture_id
    assert all(j.get("api_fixture_id") is None for j in jogos)


# ═════════════════════════════════════════════════════════════════════════
# Ciclo 5: API failure with existing jogos — no duplicates
# ═════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_ensure_setup_api_failure_existing_unchanged():
    """Quando API falha e já há jogos no banco, o fallback para MATCHES não
    cria duplicatas (ids existentes são pulados).
    """
    bb = _make_bb()
    bb._store["jogos"] = [
        {
            "id": 1,
            "match_id": "R1-01",
            "casa": "Brasil",
            "fora": "Argentina",
            "gols_casa": None,
            "gols_fora": None,
            "status": "agendado",
        },
    ]

    with patch("bolao.bigbase.fetch_from_api",
               new=AsyncMock(side_effect=RuntimeError("API offline"))):
        await bb.ensure_setup()

    jogos = _jogos_no_store(bb)
    # Deve ter 1 (existente) + 71 (novos do MATCHES) = 72
    assert len(jogos) == 72
    # O existente não foi recriado
    j1 = next(j for j in jogos if j["match_id"] == "R1-01")
    assert j1["id"] == 1


# ═════════════════════════════════════════════════════════════════════════
# Ciclo 6: API success updates scores for finished games
# ═════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_ensure_setup_api_updates_scores():
    """Quando a API retorna placar para jogo já existente, os gols são
    atualizados via patch.
    """
    bb = _make_bb()
    bb._store["jogos"] = [
        {
            "id": 1,
            "api_fixture_id": "1001",
            "match_id": "R1-01",
            "casa": "Brasil",
            "fora": "Argentina",
            "gols_casa": None,
            "gols_fora": None,
            "status": "agendado",
        },
    ]

    api_data = [
        _api_fixture("R1-01", "1001", "Brasil", "Argentina",
                      gols_casa=3, gols_fora=1, status="encerrado"),
    ]

    with patch("bolao.bigbase.fetch_from_api", new=AsyncMock(return_value=api_data)):
        await bb.ensure_setup()

    jogos = _jogos_no_store(bb)
    assert len(jogos) == 1
    assert jogos[0]["gols_casa"] == 3
    assert jogos[0]["gols_fora"] == 1
    assert jogos[0]["status"] == "encerrado"
