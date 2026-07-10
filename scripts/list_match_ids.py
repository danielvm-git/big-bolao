#!/usr/bin/env python3
"""Lista todos os jogos com match_id, times, data, status e placar.

Uso:
    python3 scripts/list_match_ids.py              # todos os jogos
    python3 scripts/list_match_ids.py Argentina     # filtra por time
    python3 scripts/list_match_ids.py --agendado    # so jogos nao iniciados
    python3 scripts/list_match_ids.py --encerrado   # so jogos finalizados
"""
from __future__ import annotations

import asyncio
import sys

from bolao.bigbase import BigBase


def _fmt(j: dict) -> str:
    mid = j.get("match_id", "?")
    casa = j.get("casa", "?")
    fora = j.get("fora", "?")
    status = j.get("status", "?")
    gc = j.get("gols_casa")
    gf = j.get("gols_fora")
    placar = f"{gc}x{gf}" if gc is not None and gf is not None else "-x-"
    kickoff = (j.get("kickoff") or "")[:16]
    return f"{mid:12s} {casa:25s} x {fora:25s}  {kickoff}  {placar:5s}  {status}"


async def main() -> None:
    filtro_time = None
    filtro_status = None

    for arg in sys.argv[1:]:
        if arg == "--agendado":
            filtro_status = "agendado"
        elif arg == "--encerrado":
            filtro_status = "encerrado"
        else:
            filtro_time = arg.lower()

    bb = BigBase()
    await bb._login()
    jogos = await bb.get_jogos()
    jogos.sort(key=lambda j: j.get("kickoff", ""))

    for j in jogos:
        casa = (j.get("casa") or "").lower()
        fora = (j.get("fora") or "").lower()
        status = j.get("status", "")

        if filtro_time and filtro_time not in casa and filtro_time not in fora:
            continue
        if filtro_status and status != filtro_status:
            continue

        print(_fmt(j))


if __name__ == "__main__":
    asyncio.run(main())
