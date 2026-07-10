#!/usr/bin/env python3
"""Adiciona um jogo no BigBase manualmente.

Uso:
    python3 scripts/add_match.py R16-06 "Portugal" "Spain" "2026-07-06T20:00:00"
    python3 scripts/add_match.py QF-01 "Canada" "Paraguay/France" "2026-07-09T21:00:00"

Argumentos:
    match_id   — identificador do jogo (ex: R16-06, QF-01, SF-01, FIN, 3P)
    casa       — time da casa
    fora       — time visitante
    kickoff    — data/hora ISO no fuso BRT (ex: 2026-07-06T20:00:00)
    [rodada]   — número da rodada (opcional, default: extrai do match_id)

Flags:
    --aberto   — marca como aberto pra palpite (default: agendado)
"""
from __future__ import annotations

import asyncio
import sys

from bolao.bigbase import JOGOS, BigBase

# Mapa de prefixo → rodada
_PHASE_RODADA = {
    "R16": 5,
    "QF": 6,
    "SF": 7,
    "3P": 8,
    "FIN": 8,
}


def _rodada(match_id: str) -> int:
    prefix = match_id.split("-")[0] if "-" in match_id else match_id
    return _PHASE_RODADA.get(prefix, 4)


async def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = set(a for a in sys.argv[1:] if a.startswith("--"))

    if len(args) < 4:
        print(__doc__.strip())
        sys.exit(1)

    match_id = args[0]
    casa = args[1]
    fora = args[2]
    kickoff = args[3]
    rodada = int(args[4]) if len(args) > 4 else _rodada(match_id)
    status = "aberto" if "--aberto" in flags else "agendado"

    jogo = {
        "match_id": match_id,
        "casa": casa,
        "fora": fora,
        "kickoff": kickoff,
        "status": status,
        "rodada": rodada,
        "gols_casa": None,
        "gols_fora": None,
    }

    bb = BigBase()
    await bb._login()

    # Verifica se já existe
    existente = await bb.get_jogo(match_id)
    if existente:
        print(f"⚠️  Jogo {match_id} já existe: {existente.get('casa')} x {existente.get('fora')}")
        return

    await bb.create(JOGOS, jogo)
    print(f"✅ {match_id:8s} {casa:25s} x {fora:25s}  {kickoff}  {status}")


if __name__ == "__main__":
    asyncio.run(main())
