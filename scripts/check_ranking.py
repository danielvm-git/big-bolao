"""Teste offline: valida a regra de pontuacao e recalcula o ranking da Rodada 1.

A planilha manual estava com o ranking errado; o calculo abaixo e a fonte da
verdade (3 = placar exato, 1 = vencedor/empate, 0 = erro). Nao acessa rede.
    python -m scripts.check_ranking
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bolao.historico import PARTICIPANTES, RODADA1, parse_placar
from bolao.scoring import pontos

# Casos unitarios da regra: (palpite, real, pontos_esperados)
CASOS = [
    ((2, 1), (2, 1), 3),   # placar exato
    ((2, 0), (3, 1), 1),   # acertou vencedor (casa), placar errado
    ((0, 0), (1, 1), 1),   # acertou empate, placar errado
    ((1, 1), (1, 1), 3),   # empate exato
    ((2, 1), (0, 2), 0),   # errou tudo
    ((0, 1), (2, 0), 0),   # inverteu o vencedor
]


def testa_regra() -> bool:
    ok = True
    for (pc, pf), (rc, rf), esp in CASOS:
        got = pontos(pc, pf, rc, rf)
        status = "ok" if got == esp else f"ERRO (esperado {esp})"
        if got != esp:
            ok = False
        print(f"  {pc}x{pf} vs {rc}x{rf} -> {got} pts [{status}]")
    return ok


def ranking_r1() -> list[tuple[str, int, int]]:
    tot = {n: [0, 0] for n in PARTICIPANTES}  # [pontos, exatos]
    for _mid, res, palps in RODADA1:
        real = parse_placar(res)
        if real is None:
            continue
        for nome, p in zip(PARTICIPANTES, palps):
            pp = parse_placar(p)
            if pp is None:
                continue
            pts = pontos(pp[0], pp[1], real[0], real[1])
            tot[nome][0] += pts
            if pts == 3:
                tot[nome][1] += 1
    rows = [(n, v[0], v[1]) for n, v in tot.items()]
    return sorted(rows, key=lambda r: (-r[1], -r[2], r[0].lower()))


def main() -> int:
    print("== Teste da regra de pontuacao ==")
    regra_ok = testa_regra()

    print("\n== Ranking recalculado (Rodada 1) ==")
    for i, (nome, pts, exatos) in enumerate(ranking_r1(), 1):
        print(f"  {i}o {nome:12} {pts:3d} pts  ({exatos} exatos)")

    if not regra_ok:
        print("\n❌ Regra de pontuacao com erro.")
        return 1
    print("\n✅ Regra validada. Ranking acima e a fonte da verdade.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
