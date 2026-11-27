"""The site's data API: public reads, bets only with a signed link."""
import asyncio

import pytest

from bolao import links, web_api
from bolao.store import SqliteStore

SECRET = "test-secret"


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr("bolao.config.LINK_SECRET", SECRET)
    s = SqliteStore(str(tmp_path / "bolao.db"))
    asyncio.run(s.create("participantes", {"telegram_id": 7, "nome": "Ana", "ativo": True}))
    asyncio.run(s.create("jogos", {"match_id": "OPEN", "kickoff": "2099-06-11T16:00:00", "status": "agendado"}))
    asyncio.run(s.create("jogos", {"match_id": "PAST", "kickoff": "2020-06-11T16:00:00", "status": "agendado"}))
    yield s
    asyncio.run(s.close())


def bet(**kw):
    body = {"uid": 7, "sig": links.sign(7, SECRET), "match_id": "OPEN", "gols_casa": 2, "gols_fora": 1}
    body.update(kw)
    return body


def test_reads_are_public(store):
    status, payload = web_api.handle_get(store, "/api/collections/jogos")
    assert status == 200 and len(payload["data"]) == 2


def test_unknown_path_is_404(store):
    assert web_api.handle_get(store, "/api/collections/secrets")[0] == 404
    assert web_api.handle_post(store, "/api/collections/palpites", bet())[0] == 404


def test_signed_bet_is_saved_with_the_stored_name(store):
    assert web_api.handle_post(store, "/api/palpite", bet(nome="Mallory")) == (200, {"ok": True})
    (p,) = asyncio.run(store.get_palpites())
    assert (p["telegram_id"], p["nome"], p["gols_casa"]) == (7, "Ana", 2)


def test_forged_uid_is_rejected(store):
    assert web_api.handle_post(store, "/api/palpite", bet(uid=8))[0] == 403


def test_closed_match_is_rejected(store):
    assert web_api.handle_post(store, "/api/palpite", bet(match_id="PAST"))[0] == 409


def test_bad_scores_are_rejected(store):
    assert web_api.handle_post(store, "/api/palpite", bet(gols_casa=-1))[0] == 400
    assert web_api.handle_post(store, "/api/palpite", bet(gols_fora="x"))[0] == 400
    assert web_api.handle_post(store, "/api/palpite", None)[0] == 400


def test_non_participant_is_rejected(store, monkeypatch):
    body = bet(uid=99, sig=links.sign(99, SECRET))
    assert web_api.handle_post(store, "/api/palpite", body)[0] == 403
