"""Helpers de tempo e formatacao."""
from __future__ import annotations

from datetime import datetime

from bolao import config

_DIAS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


def agora() -> datetime:
    return datetime.now(config.TZ)


def kickoff_dt(jogo: dict) -> datetime:
    """Parseia o kickoff ISO local (BRT) num datetime com fuso."""
    return datetime.fromisoformat(jogo["kickoff"]).replace(tzinfo=config.TZ)


def aberto_para_palpite(jogo: dict, ref: datetime | None = None) -> bool:
    """Palpite vale enquanto o jogo nao comecou e ainda nao foi encerrado."""
    if jogo.get("status") == "encerrado":
        return False
    return kickoff_dt(jogo) > (ref or agora())


def label_jogo(jogo: dict, com_horario: bool = True) -> str:
    base = f"{jogo['casa']} x {jogo['fora']}"
    if not com_horario:
        return base
    dt = kickoff_dt(jogo)
    return f"{base} · {_DIAS[dt.weekday()]} {dt:%d/%m %H:%M}"


def label_placar(jogo: dict) -> str:
    return f"{jogo['casa']} {jogo['gols_casa']} x {jogo['gols_fora']} {jogo['fora']}"
