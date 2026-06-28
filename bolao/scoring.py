"""Regras de pontuacao do bolao (sem dependencias de I/O)."""

# Fase de grupos (default)
PTS_EXATO = 3
PTS_VENCEDOR = 1

# Phase prefix → (pts_exato, pts_vencedor)
# Knockouts escalam progressivamente; SF e 3P compartilham mesma pontuacao.
FASE_PONTOS: dict[str, tuple[int, int]] = {
    "R32": (5,  2),
    "R16": (10, 5),
    "QF":  (15, 10),
    "SF":  (25, 15),
    "3P":  (25, 15),
    "FIN": (50, 25),
}


def _sinal(casa: int, fora: int) -> int:
    """1 = casa vence, 0 = empate, -1 = fora vence."""
    return (casa > fora) - (casa < fora)


def pontos(palpite_casa: int, palpite_fora: int, real_casa: int, real_fora: int,
           match_id: str = "") -> int:
    """Retorna pontos pelo palpite. Knockout stages escalam por fase via match_id prefix."""
    phase = match_id.split("-")[0] if match_id else ""
    pts_exato, pts_vencedor = FASE_PONTOS.get(phase, (PTS_EXATO, PTS_VENCEDOR))

    if palpite_casa == real_casa and palpite_fora == real_fora:
        return pts_exato
    if _sinal(palpite_casa, palpite_fora) == _sinal(real_casa, real_fora):
        return pts_vencedor
    return 0


def acertou_exato(palpite_casa: int, palpite_fora: int,
                  real_casa: int, real_fora: int) -> bool:
    """True se o palpite acertou o placar exato (independente da fase)."""
    return palpite_casa == real_casa and palpite_fora == real_fora
