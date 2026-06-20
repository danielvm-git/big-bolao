"""Publicacao de mensagens no grupo do Telegram — formatacao pura.

Toda funcao neste modulo e uma funcao pura: recebe dicts, retorna str.
Nenhuma depende de I/O, ContextTypes, ou bot.send_message.
O GroupPublisher (classe magra) so adiciona o envio.
"""
from __future__ import annotations

from bolao import ranking as ranking_mod
from bolao.scoring import pontos


def format_resultado(jogo: dict, palpites: list[dict]) -> str:
    """Formata mensagem de resultado com cravadores.

    Args:
        jogo: dict com casa, fora, gols_casa, gols_fora.
        palpites: list de dicts com nome, gols_casa, gols_fora.

    Returns:
        String HTML pronta para enviar ao grupo.
    """
    casa = jogo["casa"]
    fora = jogo["fora"]
    gc = int(jogo["gols_casa"])
    gf = int(jogo["gols_fora"])
    txt = f"⚽ <b>Fim de jogo:</b> {casa} {gc} x {gf} {fora}"
    cravadores = [
        p["nome"] for p in palpites
        if pontos(int(p["gols_casa"]), int(p["gols_fora"]), gc, gf) == 3
    ]
    if cravadores:
        txt += "\n🎯 Cravaram o placar: " + ", ".join(cravadores)
    return txt


def format_ranking(jogos: list[dict], palpites: list[dict],
                   participantes: list[dict]) -> str:
    """Formata ranking a partir de dados planos.

    Delega o calculo a ranking_mod.calcular() e a formatacao a
    ranking_mod.formatar(). Aceita dados planos em vez de ContextTypes
    para ser testavel sem mock do Telegram.
    """
    rank = ranking_mod.calcular(jogos, palpites, participantes)
    return ranking_mod.formatar(rank)


def format_lembrete(jogos: list[dict], bot_username: str) -> str:
    """Formata lembrete de jogos abertos para palpite.

    Args:
        jogos: lista de dicts com casa, fora, kickoff.
        bot_username: username do bot (sem @) para deep link.

    Returns:
        String HTML ou string vazia se lista vazia.
    """
    if not jogos:
        return ""
    linhas = ["📣 <b>Jogos abertos pra palpite (próximas 24h):</b>", ""]
    linhas += [f"• {_label_jogo_lembrete(j)}" for j in jogos]
    linhas += ["", f"👉 Palpite no privado: t.me/{bot_username} (comando /jogos)"]
    return "\n".join(linhas)


def _label_jogo_lembrete(jogo: dict) -> str:
    """Formata 'Brasil x Argentina · qui 21/06 16:00'."""
    from bolao.util import label_jogo
    return label_jogo(jogo)
