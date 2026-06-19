"""Dados historicos da Rodada 1, transcritos da planilha do grupo.

Ordem das colunas de participantes (igual ao cabecalho da planilha):
Ricardo, Mari Som, Mari Gallo, Flavia, Paje, Big, Lere.

Cada item de RODADA1 = (match_id, resultado_oficial, [palpites na ordem acima]).
String vazia = participante nao palpitou aquele jogo.
"""
from __future__ import annotations

PARTICIPANTES = ["Ricardo", "Mari Som", "Mari Gallo", "Flávia", "Pajé", "Big", "Lere"]

# (match_id, resultado, [Ricardo, MariSom, MariGallo, Flavia, Paje, Big, Lere])
RODADA1 = [
    ("R1-01", "2x0", ["2x1", "3x0", "2x1", "", "", "", ""]),
    ("R1-02", "2x1", ["1x0", "2x0", "1x1", "", "", "", ""]),
    ("R1-03", "1x1", ["0x2", "0x1", "1x2", "1x0", "", "", ""]),
    ("R1-04", "4x1", ["1x1", "1x2", "1x3", "0x2", "0x1", "", ""]),
    ("R1-05", "1x1", ["0x1", "1x0", "0x2", "1x1", "0x3", "2x2", ""]),
    ("R1-06", "1x1", ["2x0", "2x1", "2x1", "2x1", "1x0", "3x1", "3x2"]),
    ("R1-07", "0x1", ["0x2", "2x2", "1x1", "0x0", "0x4", "0x4", ""]),
    ("R1-08", "2x0", ["0x1", "0x3", "0x2", "0x3", "1x3", "0x2", ""]),
    ("R1-09", "7x1", ["4x0", "3x1", "5x0", "2x0", "4x0", "6x0", ""]),
    ("R1-10", "2x2", ["3x1", "3x2", "1x2", "1x2", "0x0", "2x3", ""]),
    ("R1-11", "1x0", ["0x1", "1x1", "1x2", "1x1", "2x2", "1x1", ""]),
    ("R1-12", "5x1", ["2x0", "2x1", "3x1", "2x1", "1x0", "3x1", ""]),
    ("R1-13", "0x0", ["4x0", "4x1", "5x0", "3x0", "2x0", "8x0", ""]),
    ("R1-14", "1x1", ["1x1", "2x1", "1x2", "2x1", "0x0", "0x1", ""]),
    ("R1-15", "1x1", ["0x3", "1x3", "1x3", "1x2", "1x3", "1x2", ""]),
    ("R1-16", "2x2", ["0x0", "1x1", "2x0", "0x0", "1x0", "3x0", ""]),
    ("R1-17", "3x1", ["2x1", "1x2", "3x0", "2x0", "2x1", "2x1", ""]),
    ("R1-18", "1x4", ["0x0", "0x0", "2x1", "1x1", "0x2", "0x2", ""]),
    ("R1-19", "3x0", ["3x0", "2x0", "3x0", "1x0", "0x0", "1x1", ""]),
    ("R1-20", "1x0", ["0x0", "1x1", "1x1", "0x0", "3x1", "3x0", ""]),
    ("R1-21", "1x1", ["3x0", "2x1", "1x0", "2x0", "2x0", "4x0", ""]),
    ("R1-22", "4x2", ["1x0", "0x2", "0x0", "1x0", "1x3", "1x1", ""]),
    ("R1-23", "1x0", ["0x0", "2x2", "2x0", "2x1", "1x0", "2x0", ""]),
    ("R1-24", "1x3", ["0x2", "0x3", "0x3", "0x2", "0x3", "1x3", ""]),
]


def parse_placar(s: str) -> tuple[int, int] | None:
    s = s.strip().lower().replace(" ", "")
    if not s or "x" not in s:
        return None
    a, b = s.split("x", 1)
    try:
        return int(a), int(b)
    except ValueError:
        return None
