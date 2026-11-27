"""Server-side data API for the site.

The browser never holds store credentials. Reads are public (the group sees
the ranking and every bet anyway). A bet is accepted only with a signed link
(see bolao.links), only for an open match, and the name comes from the store,
never from the request.
"""
from __future__ import annotations

import asyncio

from bolao import links
from bolao.bigbase import JOGOS, PALPITES, PARTICIPANTES, BigBase
from bolao.util import aberto_para_palpite, agora

READABLE = (JOGOS, PARTICIPANTES, PALPITES)
MAX_GOALS = 30


def handle_get(store: BigBase, path: str) -> tuple[int, dict]:
    parts = path.strip("/").split("/")
    if len(parts) == 3 and parts[:2] == ["api", "collections"] and parts[2] in READABLE:
        return 200, {"data": asyncio.run(store.list_records(parts[2]))}
    return 404, {"error": "not found"}


def handle_post(store: BigBase, path: str, body: object) -> tuple[int, dict]:
    if path.strip("/") != "api/palpite":
        return 404, {"error": "not found"}
    if not isinstance(body, dict):
        return 400, {"error": "invalid body"}
    uid, sig = body.get("uid"), body.get("sig")
    if not links.verify(uid, sig):
        return 403, {"error": "invalid link"}
    try:
        gc, gf = int(body["gols_casa"]), int(body["gols_fora"])
        match_id = str(body["match_id"])
    except (KeyError, TypeError, ValueError):
        return 400, {"error": "invalid bet"}
    if not (0 <= gc <= MAX_GOALS and 0 <= gf <= MAX_GOALS):
        return 400, {"error": "invalid score"}
    return asyncio.run(_save(store, int(uid), match_id, gc, gf))


async def _save(store: BigBase, uid: int, match_id: str, gc: int, gf: int) -> tuple[int, dict]:
    participante = await store.get_participante(uid)
    if not participante or participante.get("ativo") is False:
        return 403, {"error": "not a participant"}
    jogo = await store.get_jogo(match_id)
    if not jogo:
        return 404, {"error": "unknown match"}
    if not aberto_para_palpite(jogo):
        return 409, {"error": "match closed"}
    await store.salvar_palpite(match_id, uid, participante.get("nome", str(uid)),
                               gc, gf, agora().isoformat())
    return 200, {"ok": True}
