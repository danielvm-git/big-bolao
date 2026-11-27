"""SqliteStore keeps the BigBase contract: flat records, merge on patch."""
import asyncio

import pytest

from bolao.bigbase import BigBaseError
from bolao.store import SqliteStore


@pytest.fixture
def store(tmp_path):
    s = SqliteStore(str(tmp_path / "bolao.db"))
    yield s
    asyncio.run(s.close())


def test_create_and_list_return_flat_records(store):
    rid = asyncio.run(store.create("participantes", {"telegram_id": 7, "nome": "Ana", "ativo": True}))
    assert asyncio.run(store.list_records("participantes")) == [
        {"id": rid, "telegram_id": 7, "nome": "Ana", "ativo": True}]


def test_patch_merges_fields(store):
    rid = asyncio.run(store.create("jogos", {"match_id": "R1-01", "gols_casa": None, "status": "agendado"}))
    asyncio.run(store.patch("jogos", rid, {"gols_casa": 2, "status": "encerrado"}))
    (rec,) = asyncio.run(store.list_records("jogos"))
    assert rec == {"id": rid, "match_id": "R1-01", "gols_casa": 2, "status": "encerrado"}


def test_patch_missing_record_raises(store):
    with pytest.raises(BigBaseError):
        asyncio.run(store.patch("jogos", 99, {"status": "x"}))


def test_unknown_collection_is_rejected(store):
    with pytest.raises(BigBaseError):
        asyncio.run(store.list_records("users; DROP TABLE jogos"))


def test_domain_methods_work_on_sqlite(store):
    asyncio.run(store.registrar_participante(7, "Ana"))
    asyncio.run(store.create("jogos", {"match_id": "R1-01", "kickoff": "2099-06-11T16:00:00"}))
    asyncio.run(store.salvar_palpite("R1-01", 7, "Ana", 2, 1, "2026-01-01T00:00:00"))
    asyncio.run(store.salvar_palpite("R1-01", 7, "Ana", 3, 1, "2026-01-02T00:00:00"))
    assert asyncio.run(store.palpites_do_usuario(7)) == {"R1-01": (3, 1)}


def test_import_record_keeps_original_id(store):
    asyncio.run(store.import_record("palpites", 42, {"id": 42, "match_id": "R1-01"}))
    assert asyncio.run(store.list_records("palpites")) == [{"id": 42, "match_id": "R1-01"}]


def test_file_uses_wal(store):
    assert store._db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
