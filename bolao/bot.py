"""Ponto de entrada do bot do bolao (long polling)."""
from __future__ import annotations

import logging
from datetime import time as dtime

from telegram import BotCommand
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler)

from bolao import config, handlers
from bolao.betting_flow import BettingFlow, Step
from bolao.bigbase import BigBase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s")
log = logging.getLogger("bolao")


async def _post_init(app: Application) -> None:
    db = BigBase()
    app.bot_data["db"] = db
    log.info("Garantindo setup das coleches no BigBase...")
    await db.ensure_setup()
    # menu de comandos nativo do Telegram (aparece no botao "/" do chat)
    await app.bot.set_my_commands([
        BotCommand("jogos", "Palpitar nos próximos jogos"),
        BotCommand("meus", "Ver meus palpites"),
        BotCommand("ranking", "Classificação geral"),
        BotCommand("sou", "Vincular meus palpites antigos (ex: /sou Ricardo)"),
        BotCommand("start", "Começar / ajuda"),
    ])
    log.info("Bolao pronto. Provider de resultados: %s",
             config.RESULTS_PROVIDER or "manual")


async def _post_shutdown(app: Application) -> None:
    db = app.bot_data.get("db")
    if db:
        await db.close()


def build_app() -> Application:
    app = (Application.builder()
           .token(config.TELEGRAM_TOKEN)
           .post_init(_post_init)
           .post_shutdown(_post_shutdown)
           .build())

    app.add_handler(CommandHandler("start", handlers.cmd_start))
    app.add_handler(CommandHandler("ajuda", handlers.cmd_start))
    app.add_handler(CommandHandler("sou", handlers.cmd_sou))
    app.add_handler(CommandHandler("chatid", handlers.cmd_chatid))
    app.add_handler(CommandHandler("web", handlers.cmd_web))
    app.add_handler(CommandHandler("jogos", handlers.cmd_jogos))
    app.add_handler(CommandHandler("palpitar", handlers.cmd_jogos))
    app.add_handler(CommandHandler("meus", handlers.cmd_meus))
    app.add_handler(CommandHandler("ranking", handlers.cmd_ranking))
    # admin
    app.add_handler(CommandHandler("resultado", handlers.cmd_resultado))
    app.add_handler(CommandHandler("fundir", handlers.cmd_fundir))
    app.add_handler(CommandHandler("sync", handlers.cmd_sync))
    app.add_handler(CommandHandler("lembrete", handlers.cmd_lembrete))
    # fluxo de palpite (callbacks) — patterns via BettingFlow
    app.add_handler(CallbackQueryHandler(
        handlers.cb_escolher_jogo, pattern=BettingFlow.pattern_for(Step.ESCOLHER_JOGO)))
    app.add_handler(CallbackQueryHandler(
        handlers.cb_gols_casa, pattern=BettingFlow.pattern_for(Step.GOLS_CASA)))
    app.add_handler(CallbackQueryHandler(
        handlers.cb_gols_fora, pattern=BettingFlow.pattern_for(Step.GOLS_FORA)))

    # jobs periodicos
    jq = app.job_queue
    if config.RESULTS_PROVIDER:
        jq.run_repeating(handlers.job_sync, interval=1800, first=30)  # 30 min
    # lembrete diario as 12:00 BRT
    jq.run_daily(handlers.job_lembrete, time=dtime(12, 0, tzinfo=config.TZ))
    return app


def main() -> None:
    app = build_app()
    log.info("Iniciando long polling...")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
