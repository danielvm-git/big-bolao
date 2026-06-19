"""Calculo do ranking a partir de jogos encerrados e palpites."""
from __future__ import annotations

from bolao.scoring import pontos


def calcular(jogos: list[dict], palpites: list[dict],
             participantes: list[dict]) -> list[dict]:
    """Retorna lista ordenada: [{nome, telegram_id, pontos, exatos, acertos, jogos}]."""
    nomes = {int(p["telegram_id"]): p.get("nome", "?") for p in participantes}

    encerrados = {
        j["match_id"]: (int(j["gols_casa"]), int(j["gols_fora"]))
        for j in jogos
        if j.get("status") == "encerrado" and j.get("gols_casa") is not None
    }

    acc: dict[int, dict] = {}
    for p in palpites:
        mid = p["match_id"]
        if mid not in encerrados:
            continue
        tid = int(p["telegram_id"])
        rc, rf = encerrados[mid]
        pts = pontos(int(p["gols_casa"]), int(p["gols_fora"]), rc, rf)
        e = acc.setdefault(tid, {"telegram_id": tid, "pontos": 0,
                                 "exatos": 0, "acertos": 0, "jogos": 0})
        e["pontos"] += pts
        e["jogos"] += 1
        if pts == 3:
            e["exatos"] += 1
        if pts >= 1:
            e["acertos"] += 1

    # garante que todo participante aparece, mesmo zerado
    for tid, nome in nomes.items():
        acc.setdefault(tid, {"telegram_id": tid, "pontos": 0,
                             "exatos": 0, "acertos": 0, "jogos": 0})

    for tid, e in acc.items():
        e["nome"] = nomes.get(tid, p_nome_fallback(palpites, tid))

    return sorted(acc.values(),
                  key=lambda e: (-e["pontos"], -e["exatos"], e["nome"].lower()))


def p_nome_fallback(palpites: list[dict], tid: int) -> str:
    for p in palpites:
        if int(p["telegram_id"]) == tid:
            return p.get("nome", str(tid))
    return str(tid)


def formatar(rank: list[dict]) -> str:
    if not rank:
        return "Ainda nao ha pontos computados."
    medalhas = ["🥇", "🥈", "🥉"]
    linhas = ["🏆 *Ranking do Bolao*", ""]
    for i, e in enumerate(rank):
        pos = medalhas[i] if i < 3 else f"{i + 1}º"
        linhas.append(
            f"{pos} *{e['nome']}* — {e['pontos']} pts "
            f"({e['exatos']} exatos · {e['acertos']}/{e['jogos']})")
    return "\n".join(linhas)
