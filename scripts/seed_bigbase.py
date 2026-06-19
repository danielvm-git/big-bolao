"""Popula o BigBase com a agenda + resultados da Rodada 1 + palpites historicos.

Idempotente-ish: cria jogos faltantes, aplica resultados da R1 e insere os
palpites historicos sob participantes com telegram_id sintetico negativo
(-1..-7). Cada jogador real depois roda /sou <Nome> no bot pra herdar.

    python -m scripts.seed_bigbase          # sobe pra valer
    python -m scripts.seed_bigbase --dry    # so mostra o que faria
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bolao.bigbase import BigBase
from bolao.historico import PARTICIPANTES, RODADA1, parse_placar

DRY = "--dry" in sys.argv


async def main() -> None:
    db = BigBase()
    try:
        if DRY:
            print("[dry-run] nada sera escrito\n")
        else:
            print("Garantindo agenda (coleche jogos)...")
            await db.ensure_setup()

        # 1) resultados oficiais da R1
        for mid, res, _ in RODADA1:
            placar = parse_placar(res)
            if not placar:
                continue
            print(f"  resultado {mid}: {placar[0]}x{placar[1]}")
            if not DRY:
                await db.set_resultado(mid, placar[0], placar[1])

        # 2) participantes historicos (id sintetico) + palpites
        ids = {nome: -(i + 1) for i, nome in enumerate(PARTICIPANTES)}
        for nome, tid in ids.items():
            print(f"  participante {nome} (id {tid})")
            if not DRY:
                # cria direto com id sintetico (sem passar por get_participante)
                existente = await db.participante_por_nome(nome)
                if not existente:
                    from bolao.bigbase import PARTICIPANTES as COL
                    await db.create(COL, {"telegram_id": tid, "nome": nome,
                                          "ativo": False})

        for mid, _res, palps in RODADA1:
            for nome, p in zip(PARTICIPANTES, palps):
                placar = parse_placar(p)
                if not placar:
                    continue
                if not DRY:
                    await db.salvar_palpite(mid, ids[nome], nome,
                                            placar[0], placar[1], "2026-06-17T00:00:00")
        print("\nOK. Cada jogador deve rodar  /sou <Nome>  no privado do bot.")
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
