"""Regras de pontuacao do bolao (sem dependencias de I/O)."""

PTS_EXATO = 3
PTS_VENCEDOR = 1


def _sinal(casa: int, fora: int) -> int:
    """1 = casa vence, 0 = empate, -1 = fora vence."""
    return (casa > fora) - (casa < fora)


def pontos(palpite_casa: int, palpite_fora: int, real_casa: int, real_fora: int) -> int:
    """3 = placar exato, 1 = acertou vencedor/empate, 0 = errou."""
    if palpite_casa == real_casa and palpite_fora == real_fora:
        return PTS_EXATO
    if _sinal(palpite_casa, palpite_fora) == _sinal(real_casa, real_fora):
        return PTS_VENCEDOR
    return 0
