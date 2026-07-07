"""Agenda da Copa 2026 - Fase de grupos, Rodadas 1 e 2.

Extraido da agenda do Bola Rolando + planilha do grupo. Horarios em BRT.
match_id = "R<rodada>-<n>". Datas no formato ISO (ano 2026).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Match:
    match_id: str
    rodada: int
    kickoff: str  # ISO local BRT, ex "2026-06-18T13:00:00"
    casa: str
    fora: str


# (rodada, data, hora, casa, fora)
_RAW = [
    # ---- Rodada 1 ----
    (1, "2026-06-11", "16:00", "México", "África do Sul"),
    (1, "2026-06-11", "23:00", "Coreia do Sul", "República Tcheca"),
    (1, "2026-06-12", "16:00", "Canadá", "Bósnia e Herzegovina"),
    (1, "2026-06-12", "22:00", "Estados Unidos", "Paraguai"),
    (1, "2026-06-13", "16:00", "Catar", "Suíça"),
    (1, "2026-06-13", "19:00", "Brasil", "Marrocos"),
    (1, "2026-06-13", "22:00", "Haiti", "Escócia"),
    (1, "2026-06-14", "01:00", "Austrália", "Turquia"),
    (1, "2026-06-14", "14:00", "Alemanha", "Curaçao"),
    (1, "2026-06-14", "17:00", "Países Baixos", "Japão"),
    (1, "2026-06-14", "20:00", "Costa do Marfim", "Equador"),
    (1, "2026-06-14", "23:00", "Suécia", "Tunísia"),
    (1, "2026-06-15", "13:00", "Espanha", "Cabo Verde"),
    (1, "2026-06-15", "16:00", "Bélgica", "Egito"),
    (1, "2026-06-15", "19:00", "Arábia Saudita", "Uruguai"),
    (1, "2026-06-15", "22:00", "Irã", "Nova Zelândia"),
    (1, "2026-06-16", "16:00", "França", "Senegal"),
    (1, "2026-06-16", "19:00", "Iraque", "Noruega"),
    (1, "2026-06-16", "22:00", "Argentina", "Argélia"),
    (1, "2026-06-17", "01:00", "Áustria", "Jordânia"),
    (1, "2026-06-17", "14:00", "Portugal", "República Democrática do Congo"),
    (1, "2026-06-17", "17:00", "Inglaterra", "Croácia"),
    (1, "2026-06-17", "20:00", "Gana", "Panamá"),
    (1, "2026-06-17", "23:00", "Uzbequistão", "Colômbia"),
    # ---- Rodada 2 ----
    (2, "2026-06-18", "13:00", "República Tcheca", "África do Sul"),
    (2, "2026-06-18", "16:00", "Suíça", "Bósnia e Herzegovina"),
    (2, "2026-06-18", "19:00", "Canadá", "Catar"),
    (2, "2026-06-18", "22:00", "México", "Coreia do Sul"),
    (2, "2026-06-19", "16:00", "Estados Unidos", "Austrália"),
    (2, "2026-06-19", "19:00", "Escócia", "Marrocos"),
    (2, "2026-06-19", "21:30", "Brasil", "Haiti"),
    (2, "2026-06-20", "00:00", "Turquia", "Paraguai"),
    (2, "2026-06-20", "14:00", "Países Baixos", "Suécia"),
    (2, "2026-06-20", "17:00", "Alemanha", "Costa do Marfim"),
    (2, "2026-06-20", "21:00", "Equador", "Curaçao"),
    (2, "2026-06-21", "01:00", "Tunísia", "Japão"),
    (2, "2026-06-21", "13:00", "Espanha", "Arábia Saudita"),
    (2, "2026-06-21", "16:00", "Bélgica", "Irã"),
    (2, "2026-06-21", "19:00", "Uruguai", "Cabo Verde"),
    (2, "2026-06-21", "22:00", "Nova Zelândia", "Egito"),
    (2, "2026-06-22", "14:00", "Argentina", "Áustria"),
    (2, "2026-06-22", "18:00", "França", "Iraque"),
    (2, "2026-06-22", "21:00", "Noruega", "Senegal"),
    (2, "2026-06-23", "00:00", "Jordânia", "Argélia"),
    (2, "2026-06-23", "14:00", "Portugal", "Uzbequistão"),
    (2, "2026-06-23", "17:00", "Inglaterra", "Gana"),
    (2, "2026-06-23", "20:00", "Panamá", "Croácia"),
    (2, "2026-06-23", "23:00", "Colômbia", "República Democrática do Congo"),
    # ---- Rodada 3 (agenda oficial Bola Rolando; jogos do grupo simultaneos) ----
    (3, "2026-06-24", "16:00", "Suíça", "Canadá"),
    (3, "2026-06-24", "16:00", "Bósnia e Herzegovina", "Catar"),
    (3, "2026-06-24", "19:00", "Marrocos", "Haiti"),
    (3, "2026-06-24", "19:00", "Escócia", "Brasil"),
    (3, "2026-06-24", "22:00", "África do Sul", "Coreia do Sul"),
    (3, "2026-06-24", "22:00", "República Tcheca", "México"),
    (3, "2026-06-25", "17:00", "Curaçao", "Costa do Marfim"),
    (3, "2026-06-25", "17:00", "Equador", "Alemanha"),
    (3, "2026-06-25", "20:00", "Tunísia", "Países Baixos"),
    (3, "2026-06-25", "20:00", "Japão", "Suécia"),
    (3, "2026-06-25", "23:00", "Turquia", "Estados Unidos"),
    (3, "2026-06-25", "23:00", "Paraguai", "Austrália"),
    (3, "2026-06-26", "16:00", "Noruega", "França"),
    (3, "2026-06-26", "16:00", "Senegal", "Iraque"),
    (3, "2026-06-26", "21:00", "Cabo Verde", "Arábia Saudita"),
    (3, "2026-06-26", "21:00", "Uruguai", "Espanha"),
    (3, "2026-06-27", "00:00", "Nova Zelândia", "Bélgica"),
    (3, "2026-06-27", "00:00", "Egito", "Irã"),
    (3, "2026-06-27", "18:00", "Panamá", "Inglaterra"),
    (3, "2026-06-27", "18:00", "Croácia", "Gana"),
    (3, "2026-06-27", "20:30", "Colômbia", "Portugal"),
    (3, "2026-06-27", "20:30", "República Democrática do Congo", "Uzbequistão"),
    (3, "2026-06-27", "23:00", "Argélia", "Áustria"),
    (3, "2026-06-27", "23:00", "Jordânia", "Argentina"),
]


def _build() -> list[Match]:
    out: list[Match] = []
    counters: dict[int, int] = {}
    for rodada, data, hora, casa, fora in _RAW:
        counters[rodada] = counters.get(rodada, 0) + 1
        mid = f"R{rodada}-{counters[rodada]:02d}"
        out.append(Match(mid, rodada, f"{data}T{hora}:00", casa, fora))
    return out


MATCHES: list[Match] = _build()

# ---- Quartas de Final ----
_QUARTAS: list[Match] = [
    Match("QF-01", 0, "2026-07-09T17:00:00", "França", "Marrocos"),
    Match("QF-02", 0, "2026-07-10T16:00:00", "Espanha", "Bélgica"),
    Match("QF-03", 0, "2026-07-11T18:00:00", "Noruega", "Inglaterra"),
]
MATCHES.extend(_QUARTAS)

BY_ID: dict[str, Match] = {m.match_id: m for m in MATCHES}


def find_by_teams(casa: str, fora: str) -> Match | None:
    casa, fora = casa.lower().strip(), fora.lower().strip()
    for m in MATCHES:
        if casa in m.casa.lower() and fora in m.fora.lower():
            return m
    return None
