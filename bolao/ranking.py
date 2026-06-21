"""Calculo do ranking a partir de jogos encerrados e palpites."""
from __future__ import annotations

from bolao.scoring import pontos

# Telegram user IDs are always positive. Negative IDs are seed placeholders.
_VALID_TG_MIN = 0


def calcular(jogos: list[dict], palpites: list[dict],
             participantes: list[dict]) -> list[dict]:
    """Retorna lista ordenada: [{nome, telegram_id, pontos, exatos, acertos, jogos}]."""
    # So participantes ativos — inativos sao duplicatas fundidas por reivindicar.
    # Placeholders criados pelo seed tem telegram_id < 0 (nunca sao usuarios reais).
    # Dupla checagem: ativo=False OU telegram_id negativo = placeholder removido.
    ativos = [p for p in participantes
              if p.get("ativo", True) and int(p.get("telegram_id", 0)) >= _VALID_TG_MIN]
    nomes = {int(p["telegram_id"]): p.get("nome", "?") for p in ativos}

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
    for tid in nomes:
        acc.setdefault(tid, {"telegram_id": tid, "pontos": 0,
                             "exatos": 0, "acertos": 0, "jogos": 0})

    for tid, e in acc.items():
        e["nome"] = nomes.get(tid, p_nome_fallback(palpites, tid))

    # Descarta linhas de placeholders (telegram_id < _VALID_TG_MIN)
    acc = {tid: e for tid, e in acc.items() if tid >= _VALID_TG_MIN}

    return sorted(acc.values(),
                  key=lambda e: (-e["pontos"], -e["exatos"], -e["acertos"], e["jogos"]))


def p_nome_fallback(palpites: list[dict], tid: int) -> str:
    for p in palpites:
        if int(p["telegram_id"]) == tid:
            return p.get("nome", str(tid))
    return str(tid)


def formatar(rank: list[dict]) -> str:
    if not rank:
        return "Ainda nao ha pontos computados."
    w_nome = max(len(e['nome']) for e in rank)
    w_pts = max(len(str(e['pontos'])) for e in rank)
    w_ex = max(len(str(e['exatos'])) for e in rank)
    w_ac = max(len(str(e['acertos'] - e['exatos'])) for e in rank)
    w_jg = max(len(str(e['jogos'])) for e in rank)

    # 🎯 ✅ 📋 each render 2 cells wide in Telegram monospace but len()=1
    _EMOJI_IN_LINE2 = 3
    line1_width = 2 + 2 + w_nome + 2 + w_pts + 3  # "N.  <nome>  <pts>pts"

    linhas = []
    for i, e in enumerate(rank):
        pos = f"{i + 1}."
        pts_1 = e['acertos'] - e['exatos']
        nome = e['nome'].ljust(w_nome)
        pts_str = f"{str(e['pontos']).rjust(w_pts)}pts"
        linha1 = f"{pos}  {nome}  {pts_str}"
        linha2_content = (
            f"🎯{str(e['exatos']).rjust(w_ex)}"
            f"  ✅{str(pts_1).rjust(w_ac)}"
            f"  📋{str(e['jogos']).rjust(w_jg)}"
        )
        padding = line1_width - len(linha2_content) - _EMOJI_IN_LINE2
        linha2 = " " * padding + linha2_content
        linhas.append(f"{linha1}\n{linha2}")

    sep = "─" * line1_width
    footer = '\nVeja mais em <a href="https://bolao.bigbase.click">bolao.bigbase.click</a>'
    return f"<pre>🏆 Ranking do Bolao\n{sep}\n" + "\n".join(linhas) + f"</pre>{footer}"
