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

from bolao import config, results as results_mod
from bolao.betting_flow import BettingFlow, Step
from bolao.bigbase import BigBase
from bolao.group_publisher import format_lembrete, format_ranking, format_resultado
from bolao.util import (aberto_para_palpite, agora, is_quiet_hours, label_jogo, label_placar)

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
        f"⚽ <b>Bem-vindo ao Bolao, {nome}!</b>\n\n"
        "Aqui você palpita no placar exato dos jogos — <b>só você vê seus palpites</b>.\n\n"
        "<b>Comandos:</b>\n"
        "/jogos — palpitar nos próximos jogos\n"
        "/meus — ver meus palpites\n"
        "/ranking — classificação geral\n\n"
        "Pontuação: <b>3</b> placar exato · <b>1</b> acertar o vencedor/empate · <b>0</b> erro.",
        parse_mode=ParseMode.HTML)


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
            "Ex: <code>/sou Ricardo</code>\n\nParticipantes: " + ", ".join(sorted(nomes)),
            parse_mode=ParseMode.HTML)
        return
    ok = await db(context).reivindicar(nome, update.effective_user.id)
    if ok:
        await update.message.reply_text(
            f"✅ Pronto! Você agora é <b>{nome}</b> e herdou os palpites da Rodada 1.\n"
            "Veja /ranking ou palpite nos próximos com /jogos.",
            parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(f"Não achei o participante “{nome}”.")


async def cmd_chatid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"chat_id: {update.effective_chat.id}")


async def cmd_web(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia link do site do bolao com autenticacao automatica."""
    uid = update.effective_user.id
    web_url = os.environ.get("BOLAO_WEB_URL", "http://localhost:5173")
    link = f"{web_url}/?uid={uid}"
    await update.message.reply_text(
        f"🌐 <b>Acesse o Bolao pelo navegador:</b>\n\n"
        f"<a href=\"{link}\">👉 Clique aqui para abrir</a>\n\n"
        f"Ou cole este link no navegador:\n<code>{link}</code>",
        parse_mode=ParseMode.HTML)


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
            marca + label_jogo(j), callback_data=BettingFlow.serialize(Step.ESCOLHER_JOGO, match_id=j['match_id']))])
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
    linhas = ["<b>Seus palpites:</b>", ""]
    for mid, (gc, gf) in sorted(meus.items()):
        j = jogos.get(mid)
        if not j:
            continue
        linhas.append(f"• {j['casa']} <b>{gc} x {gf}</b> {j['fora']}")
    await update.message.reply_text("\n".join(linhas), parse_mode=ParseMode.HTML)


async def cmd_ranking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    d = db(context)
    texto = format_ranking(await d.get_jogos(), await d.get_palpites(),
                           await d.listar_participantes())
    await update.effective_message.reply_text(texto, parse_mode=ParseMode.HTML)


# ---------------- fluxo de palpite (inline) ----------------

def _seletor_gols_casa(match_id: str) -> InlineKeyboardMarkup:
    """Seletor de 0..MAX_GOLS gols para o time da casa."""
    nums = [InlineKeyboardButton(
        str(n), callback_data=BettingFlow.serialize(Step.GOLS_CASA, match_id=match_id, gols=n))
        for n in range(MAX_GOLS + 1)]
    linhas = [nums[i:i + 4] for i in range(0, len(nums), 4)]
    return InlineKeyboardMarkup(linhas)


def _seletor_gols_fora(match_id: str, gc: int) -> InlineKeyboardMarkup:
    """Seletor de 0..MAX_GOLS gols para o time visitante."""
    nums = [InlineKeyboardButton(
        str(n), callback_data=BettingFlow.serialize(Step.GOLS_FORA, match_id=match_id, gc=gc, gf=n))
        for n in range(MAX_GOLS + 1)]
    linhas = [nums[i:i + 4] for i in range(0, len(nums), 4)]
    return InlineKeyboardMarkup(linhas)


async def cb_escolher_jogo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    parsed = BettingFlow.deserialize(q.data)
    if parsed is None:
        await q.edit_message_text("⛔ Erro no callback.", parse_mode=ParseMode.HTML)
        return
    mid = parsed[1]["match_id"]
    jogo = await db(context).get_jogo(mid)
    if not jogo or not aberto_para_palpite(jogo):
        await q.edit_message_text("⛔ Esse jogo já começou — palpite encerrado.", parse_mode=ParseMode.HTML)
        return
    await q.edit_message_text(
        f"<b>{jogo['casa']} x {jogo['fora']}</b>\nQuantos gols do <b>{jogo['casa']}</b>?",
        parse_mode=ParseMode.HTML, reply_markup=_seletor_gols_casa(mid))


async def cb_gols_casa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    parsed = BettingFlow.deserialize(q.data)
    if parsed is None:
        await q.edit_message_text("⛔ Erro no callback.", parse_mode=ParseMode.HTML)
        return
    mid = parsed[1]["match_id"]
    gols = parsed[1]["gols"]
    jogo = await db(context).get_jogo(mid)
    if not jogo or not aberto_para_palpite(jogo):
        await q.edit_message_text("⛔ Esse jogo já começou — palpite encerrado.", parse_mode=ParseMode.HTML)
        return
    await q.edit_message_text(
        f"<b>{jogo['casa']} {gols} x ? {jogo['fora']}</b>\nQuantos gols do <b>{jogo['fora']}</b>?",
        parse_mode=ParseMode.HTML, reply_markup=_seletor_gols_fora(mid, gols))


async def cb_gols_fora(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    parsed = BettingFlow.deserialize(q.data)
    if parsed is None:
        await q.answer()
        await q.edit_message_text("⛔ Erro no callback.", parse_mode=ParseMode.HTML)
        return
    mid = parsed[1]["match_id"]
    gc = parsed[1]["gc"]
    gf = parsed[1]["gf"]
    try:
        jogo = await db(context).get_jogo(mid)
    except Exception:
        await q.answer("Erro de conexão. ⛔")
        await q.edit_message_text("⛔ Erro de conexão com o banco de dados.", parse_mode=ParseMode.HTML)
        logging.getLogger("bolao").error("Erro ao obter jogo %s", mid, exc_info=True)
        return

    if not jogo or not aberto_para_palpite(jogo):
        await q.answer()
        await q.edit_message_text("⛔ Esse jogo já começou — palpite encerrado.", parse_mode=ParseMode.HTML)
        return
    user = update.effective_user
    nome = user.full_name or user.username or str(user.id)
    try:
        await db(context).salvar_palpite(mid, user.id, nome, gc, gf,
                                         agora().isoformat())
    except Exception:
        await q.answer("Erro ao salvar palpite. ⛔")
        await q.edit_message_text("⛔ Erro de conexão com o banco de dados.", parse_mode=ParseMode.HTML)
        logging.getLogger("bolao").error("Erro ao salvar palpite para %s", user.id, exc_info=True)
        return

    await q.answer("Palpite salvo! ✅")
    await q.edit_message_text(
        f"✅ Palpite salvo:\n<b>{jogo['casa']} {gc} x {gf} {jogo['fora']}</b>\n\n"
        "Use /jogos pra palpitar em outro.", parse_mode=ParseMode.HTML)


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
        await update.message.reply_text(f"match_id <code>{mid}</code> não encontrado.",
                                        parse_mode=ParseMode.HTML)
        return
    jogo = await db(context).get_jogo(mid)
    await update.message.reply_text(f"✅ Resultado salvo: {label_placar(jogo)}")
    await _publicar_resultado(context, jogo, manual=True)


async def cmd_sync(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not config.is_admin(update.effective_user.id):
        return
    await update.message.reply_text("🔄 Buscando resultados...")
    novos = await _sync_resultados(context, manual=True)
    await update.message.reply_text(
        f"{novos} novo(s) resultado(s) aplicado(s)." if novos
        else "Nenhum resultado novo encontrado.")


async def cmd_lembrete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not config.is_admin(update.effective_user.id):
        return
    await _postar_lembrete(context)
    await update.message.reply_text("Lembrete postado no grupo. 📣")


# ---------------- jobs / publicacoes no grupo ----------------

async def _sync_resultados(context: ContextTypes.DEFAULT_TYPE, manual: bool = False) -> int:
    d = db(context)
    jogos_list = await d.get_jogos()
    novos = 0
    for res in await results_mod.buscar_encerrados(jogos_list):
        await d.set_resultado(res.match_id, res.gols_casa, res.gols_fora)
        j2 = await d.get_jogo(res.match_id)
        try:
            await _publicar_resultado(context, j2, manual=manual)
        except Exception:
            logging.getLogger("bolao").warning(
                "Falha ao publicar resultado %s no grupo", res.match_id, exc_info=True)
        novos += 1
    if novos:
        try:
            await _publicar_ranking(context, manual=manual)
        except Exception:
            logging.getLogger("bolao").warning("Falha ao publicar ranking no grupo", exc_info=True)
    return novos


async def _publicar_resultado(context: ContextTypes.DEFAULT_TYPE, jogo: dict,
                              manual: bool = False) -> None:
    if not config.GRUPO_CHAT_ID:
        return
    d = db(context)
    palp = [p for p in await d.get_palpites() if p["match_id"] == jogo["match_id"]]
    texto = format_resultado(jogo, palp)
    if not manual and is_quiet_hours():
        context.bot_data.setdefault("pending_results", []).append(
            {"texto": texto, "parse_mode": ParseMode.HTML})
        logging.getLogger("bolao").info("Publicação enfileirada (quiet hours)")
        return
    await context.bot.send_message(config.GRUPO_CHAT_ID, texto, parse_mode=ParseMode.HTML)


async def _publicar_ranking(context: ContextTypes.DEFAULT_TYPE,
                            manual: bool = False) -> None:
    if not config.GRUPO_CHAT_ID:
        return
    d = db(context)
    texto = format_ranking(await d.get_jogos(), await d.get_palpites(),
                           await d.listar_participantes())
    if not manual and is_quiet_hours():
        context.bot_data.setdefault("pending_results", []).append(
            {"texto": texto, "parse_mode": ParseMode.HTML})
        logging.getLogger("bolao").info("Publicação enfileirada (quiet hours)")
        return
    await context.bot.send_message(config.GRUPO_CHAT_ID, texto,
                                   parse_mode=ParseMode.HTML)


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
    texto = format_lembrete(proximos, me.username)
    await context.bot.send_message(config.GRUPO_CHAT_ID, texto,
                                   parse_mode=ParseMode.HTML)


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


async def job_morning_flush(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Dispara às 08:00 BRT: drena mensagens enfileiradas durante quiet hours."""
    import asyncio
    fila = context.bot_data.get("pending_results", [])
    if not fila or not config.GRUPO_CHAT_ID:
        context.bot_data["pending_results"] = []
        return
    log = logging.getLogger("bolao")
    log.info("Morning flush: enviando %d publicação(ões) enfileirada(s)", len(fila))
    for i, item in enumerate(fila):
        try:
            await context.bot.send_message(
                config.GRUPO_CHAT_ID, item["texto"], parse_mode=item["parse_mode"])
        except Exception:
            log.warning("Falha ao enviar publicação enfileirada", exc_info=True)
        if i < len(fila) - 1:
            await asyncio.sleep(2)
    context.bot_data["pending_results"] = []
