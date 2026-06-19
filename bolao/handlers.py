"""Handlers do bot do bolao.

Privacidade / anti-flood: TODO o fluxo de palpite acontece no chat privado com o
bot. No grupo o bot so reage a /ranking, e os comandos de palpite redirecionam a
pessoa pro privado (com botao de deep-link). Ninguem ve o palpite de ninguem.
"""
from __future__ import annotations

import logging
import os

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bolao import config, ranking as ranking_mod, results as results_mod
from bolao.bigbase import BigBase
from bolao.util import (aberto_para_palpite, agora, label_jogo, label_placar)

MAX_GOLS = 7  # 0..7 no seletor


def db(context: ContextTypes.DEFAULT_TYPE) -> BigBase:
    return context.application.bot_data["db"]


def _privado(update: Update) -> bool:
    return update.effective_chat.type == "private"


async def _link_privado(update: Update, context: ContextTypes.DEFAULT_TYPE,
                        texto: str) -> None:
    me = await context.bot.get_me()
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(
        "📲 Abrir conversa com o bot", url=f"https://t.me/{me.username}")]])
    await update.effective_message.reply_text(texto, reply_markup=kb)


# ---------------- comandos basicos ----------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _privado(update):
        await _link_privado(update, context,
                            "Fala comigo no privado pra participar do bolao 👇")
        return
    user = update.effective_user
    nome = user.full_name or user.username or str(user.id)
    await db(context).registrar_participante(user.id, nome)
    await update.message.reply_text(
        f"⚽ *Bem-vindo ao Bolao, {nome}!*\n\n"
        "Aqui você palpita no placar exato dos jogos — *só você vê seus palpites*.\n\n"
        "*Comandos:*\n"
        "/jogos — palpitar nos próximos jogos\n"
        "/meus — ver meus palpites\n"
        "/ranking — classificação geral\n\n"
        "Pontuação: *3* placar exato · *1* acertar o vencedor/empate · *0* erro.",
        parse_mode=ParseMode.MARKDOWN)


async def cmd_sou(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Vincula a conta do usuario a um participante historico (palpites da R1)."""
    if not _privado(update):
        await _link_privado(update, context, "Use /sou aqui no privado 🙏")
        return
    nome = " ".join(context.args).strip()
    if not nome:
        nomes = [p["nome"] for p in await db(context).listar_participantes()]
        await update.message.reply_text(
            "Diga quem você é pra herdar seus palpites da Rodada 1.\n"
            "Ex: `/sou Ricardo`\n\nParticipantes: " + ", ".join(sorted(nomes)),
            parse_mode=ParseMode.MARKDOWN)
        return
    ok = await db(context).reivindicar(nome, update.effective_user.id)
    if ok:
        await update.message.reply_text(
            f"✅ Pronto! Você agora é *{nome}* e herdou os palpites da Rodada 1.\n"
            "Veja /ranking ou palpite nos próximos com /jogos.",
            parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(f"Não achei o participante “{nome}”.")


async def cmd_chatid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"chat_id: `{update.effective_chat.id}`",
                                    parse_mode=ParseMode.MARKDOWN)


async def cmd_web(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia link do site do bolao com autenticacao automatica."""
    uid = update.effective_user.id
    web_url = os.environ.get("BOLAO_WEB_URL", "http://localhost:5173")
    link = f"{web_url}/?uid={uid}"
    await update.message.reply_text(
        f"🌐 *Acesse o Bolao pelo navegador:*\n\n"
        f"[👉 Clique aqui para abrir]({link})\n\n"
        f"Ou cole este link no navegador:\n`{link}`",
        parse_mode=ParseMode.MARKDOWN)


async def cmd_jogos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _privado(update):
        await _link_privado(update, context,
                            "Os palpites são no privado pra não floodar o grupo 🙏")
        return
    jogos = [j for j in await db(context).get_jogos() if aberto_para_palpite(j)]
    if not jogos:
        await update.message.reply_text("Nenhum jogo aberto pra palpite no momento. ⏳")
        return
    meus = await db(context).palpites_do_usuario(update.effective_user.id)
    botoes = []
    for j in jogos[:30]:
        marca = "✅ " if j["match_id"] in meus else "▫️ "
        botoes.append([InlineKeyboardButton(
            marca + label_jogo(j), callback_data=f"g|{j['match_id']}")])
    await update.message.reply_text(
        "Escolha um jogo pra palpitar (✅ = já palpitado):",
        reply_markup=InlineKeyboardMarkup(botoes))


async def cmd_meus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _privado(update):
        await _link_privado(update, context, "Te mostro seus palpites no privado 🤫")
        return
    meus = await db(context).palpites_do_usuario(update.effective_user.id)
    if not meus:
        await update.message.reply_text("Você ainda não palpitou. Use /jogos 😉")
        return
    jogos = {j["match_id"]: j for j in await db(context).get_jogos()}
    linhas = ["*Seus palpites:*", ""]
    for mid, (gc, gf) in sorted(meus.items()):
        j = jogos.get(mid)
        if not j:
            continue
        linhas.append(f"• {j['casa']} *{gc} x {gf}* {j['fora']}")
    await update.message.reply_text("\n".join(linhas), parse_mode=ParseMode.MARKDOWN)


async def cmd_ranking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    texto = await _montar_ranking(context)
    await update.effective_message.reply_text(texto, parse_mode=ParseMode.MARKDOWN)


async def _montar_ranking(context: ContextTypes.DEFAULT_TYPE) -> str:
    d = db(context)
    rank = ranking_mod.calcular(await d.get_jogos(), await d.get_palpites(),
                                await d.listar_participantes())
    return ranking_mod.formatar(rank)


# ---------------- fluxo de palpite (inline) ----------------

def _seletor(prefixo: str, titulo: str) -> InlineKeyboardMarkup:
    nums = [InlineKeyboardButton(str(n), callback_data=f"{prefixo}|{n}")
            for n in range(MAX_GOLS + 1)]
    linhas = [nums[i:i + 4] for i in range(0, len(nums), 4)]
    return InlineKeyboardMarkup(linhas)


async def cb_escolher_jogo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    mid = q.data.split("|", 1)[1]
    jogo = await db(context).get_jogo(mid)
    if not jogo or not aberto_para_palpite(jogo):
        await q.edit_message_text("⛔ Esse jogo já começou — palpite encerrado.")
        return
    await q.edit_message_text(
        f"*{jogo['casa']} x {jogo['fora']}*\nQuantos gols do *{jogo['casa']}*?",
        parse_mode=ParseMode.MARKDOWN, reply_markup=_seletor(f"h|{mid}", jogo["casa"]))


async def cb_gols_casa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    _, mid, n = q.data.split("|")
    jogo = await db(context).get_jogo(mid)
    if not jogo or not aberto_para_palpite(jogo):
        await q.edit_message_text("⛔ Esse jogo já começou — palpite encerrado.")
        return
    await q.edit_message_text(
        f"*{jogo['casa']} {n} x ? {jogo['fora']}*\nQuantos gols do *{jogo['fora']}*?",
        parse_mode=ParseMode.MARKDOWN, reply_markup=_seletor(f"f|{mid}|{n}", jogo["fora"]))


async def cb_gols_fora(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    _, mid, gc, gf = q.data.split("|")
    jogo = await db(context).get_jogo(mid)
    if not jogo or not aberto_para_palpite(jogo):
        await q.answer()
        await q.edit_message_text("⛔ Esse jogo já começou — palpite encerrado.")
        return
    user = update.effective_user
    nome = user.full_name or user.username or str(user.id)
    await db(context).salvar_palpite(mid, user.id, nome, int(gc), int(gf),
                                     agora().isoformat())
    await q.answer("Palpite salvo! ✅")
    await q.edit_message_text(
        f"✅ Palpite salvo:\n*{jogo['casa']} {gc} x {gf} {jogo['fora']}*\n\n"
        "Use /jogos pra palpitar em outro.", parse_mode=ParseMode.MARKDOWN)


# ---------------- admin ----------------

async def cmd_resultado(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not config.is_admin(update.effective_user.id):
        return
    try:
        mid, gc, gf = context.args[0], int(context.args[1]), int(context.args[2])
    except (IndexError, ValueError):
        await update.message.reply_text("Uso: /resultado <match_id> <gols_casa> <gols_fora>")
        return
    if not await db(context).set_resultado(mid, gc, gf):
        await update.message.reply_text(f"match_id `{mid}` não encontrado.",
                                        parse_mode=ParseMode.MARKDOWN)
        return
    jogo = await db(context).get_jogo(mid)
    await update.message.reply_text(f"✅ Resultado salvo: {label_placar(jogo)}")
    await _publicar_resultado(context, jogo)


async def cmd_sync(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not config.is_admin(update.effective_user.id):
        return
    await update.message.reply_text("🔄 Buscando resultados...")
    novos = await _sync_resultados(context)
    await update.message.reply_text(
        f"{novos} novo(s) resultado(s) aplicado(s)." if novos
        else "Nenhum resultado novo encontrado.")


async def cmd_lembrete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not config.is_admin(update.effective_user.id):
        return
    await _postar_lembrete(context)
    await update.message.reply_text("Lembrete postado no grupo. 📣")


# ---------------- jobs / publicacoes no grupo ----------------

async def _sync_resultados(context: ContextTypes.DEFAULT_TYPE) -> int:
    d = db(context)
    jogos = {j["match_id"]: j for j in await d.get_jogos()}
    novos = 0
    for res in await results_mod.buscar_encerrados():
        j = jogos.get(res.match.match_id)
        if j and j.get("status") != "encerrado":
            await d.set_resultado(res.match.match_id, res.gols_casa, res.gols_fora)
            j2 = await d.get_jogo(res.match.match_id)
            await _publicar_resultado(context, j2)
            novos += 1
    if novos:
        await _publicar_ranking(context)
    return novos


async def _publicar_resultado(context: ContextTypes.DEFAULT_TYPE, jogo: dict) -> None:
    if not config.GRUPO_CHAT_ID:
        return
    d = db(context)
    palp = [p for p in await d.get_palpites() if p["match_id"] == jogo["match_id"]]
    rc, rf = int(jogo["gols_casa"]), int(jogo["gols_fora"])
    from bolao.scoring import pontos
    cravaram = [p["nome"] for p in palp
                if pontos(int(p["gols_casa"]), int(p["gols_fora"]), rc, rf) == 3]
    txt = f"⚽ *Fim de jogo:* {label_placar(jogo)}"
    if cravaram:
        txt += "\n🎯 Cravaram o placar: " + ", ".join(cravaram)
    await context.bot.send_message(config.GRUPO_CHAT_ID, txt, parse_mode=ParseMode.MARKDOWN)


async def _publicar_ranking(context: ContextTypes.DEFAULT_TYPE) -> None:
    if not config.GRUPO_CHAT_ID:
        return
    await context.bot.send_message(config.GRUPO_CHAT_ID, await _montar_ranking(context),
                                   parse_mode=ParseMode.MARKDOWN)


async def _postar_lembrete(context: ContextTypes.DEFAULT_TYPE) -> None:
    if not config.GRUPO_CHAT_ID:
        return
    ref = agora()
    proximos = [j for j in await db(context).get_jogos()
                if aberto_para_palpite(j, ref)
                and (kickoff_horas(j, ref)) <= 24][:8]
    me = await context.bot.get_me()
    if not proximos:
        return
    linhas = ["📣 *Jogos abertos pra palpite (próximas 24h):*", ""]
    linhas += [f"• {label_jogo(j)}" for j in proximos]
    linhas += ["", f"👉 Palpite no privado: t.me/{me.username} (comando /jogos)"]
    await context.bot.send_message(config.GRUPO_CHAT_ID, "\n".join(linhas),
                                   parse_mode=ParseMode.MARKDOWN)


def kickoff_horas(jogo: dict, ref) -> float:
    from bolao.util import kickoff_dt
    return (kickoff_dt(jogo) - ref).total_seconds() / 3600


async def job_sync(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job periodico: puxa resultados e publica."""
    try:
        await _sync_resultados(context)
    except Exception:  # noqa: BLE001
        logging.getLogger("bolao").warning("job_sync falhou", exc_info=True)


async def job_lembrete(context: ContextTypes.DEFAULT_TYPE) -> None:
    await _postar_lembrete(context)
