"""Ponto de entrada do bot do bolao (long polling)."""
from __future__ import annotations

from datetime import time as dtime

from telegram import BotCommand
from telegram.error import Conflict
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler, ContextTypes)

from bolao import config, handlers
from bolao import util
from bolao.betting_flow import BettingFlow, Step
from bolao.bigbase import BigBase
from bolao.logger import get_logger
from bolao.util import version

log = get_logger("bolao.bot")


async def _post_init(app: Application) -> None:
    log.info(f"Starting Big Bolao {version()}")
    db = BigBase()
    app.bot_data["db"] = db
    app.bot_data["pending_results"] = []
    log.info("Setting up BigBase collections")
    await db.ensure_setup()
    # menu de comandos nativo do Telegram (aparece no botao "/" do chat)
    await app.bot.set_my_commands([
        BotCommand("jogos", "Palpitar nos próximos jogos"),
        BotCommand("meus", "Ver meus palpites"),
        BotCommand("ranking", "Classificação geral"),
        BotCommand("sou", "Vincular meus palpites antigos (ex: /sou Ricardo)"),
        BotCommand("start", "Começar / ajuda"),
    ])
    log.info("Bot ready", extra={
        "provider": config.RESULTS_PROVIDER or "manual",
        "quiet_hours_start": util.QUIET_START,
        "quiet_hours_end": util.QUIET_END,
    })


async def _post_shutdown(app: Application) -> None:
    db = app.bot_data.get("db")
    if db:
        await db.close()


async def _handle_error(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log polling errors, especially 409 Conflict (another instance is polling)."""
    error = context.error
    if isinstance(error, Conflict):
        log.error(
            "Conflict detected: another instance is polling this token. "
            "Ensure only one bot instance is running.",
            exc_info=error
        )
    else:
        log.error(f"Unhandled error: {error}", exc_info=error)


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
    app.add_handler(CommandHandler("version", handlers.cmd_version))
    app.add_handler(CommandHandler("web", handlers.cmd_web))
    app.add_handler(CommandHandler("jogos", handlers.cmd_jogos))
    app.add_handler(CommandHandler("palpitar", handlers.cmd_jogos))
    app.add_handler(CommandHandler("meus", handlers.cmd_meus))
    app.add_handler(CommandHandler("ranking", handlers.cmd_ranking))
    # admin
    app.add_handler(CommandHandler("resultado", handlers.cmd_resultado))
    app.add_handler(CommandHandler("matchid", handlers.cmd_matchid))
    app.add_handler(CommandHandler("sync", handlers.cmd_sync))
    app.add_handler(CommandHandler("lembrete", handlers.cmd_lembrete))
    # fluxo de palpite (callbacks) — patterns via BettingFlow
    app.add_handler(CallbackQueryHandler(
        handlers.cb_escolher_jogo, pattern=BettingFlow.pattern_for(Step.ESCOLHER_JOGO)))
    app.add_handler(CallbackQueryHandler(
        handlers.cb_gols_casa, pattern=BettingFlow.pattern_for(Step.GOLS_CASA)))
    app.add_handler(CallbackQueryHandler(
        handlers.cb_gols_fora, pattern=BettingFlow.pattern_for(Step.GOLS_FORA)))

    # error handler for polling conflicts and other errors
    app.add_error_handler(_handle_error)

    # jobs periodicos
    jq = app.job_queue
    if config.RESULTS_PROVIDER:
        jq.run_repeating(handlers.job_sync, interval=1800, first=30)   # 30 min
    jq.run_repeating(handlers.job_sync_fixtures, interval=3600, first=60)  # 1h
    # lembrete diario as 12:00 BRT
    jq.run_daily(handlers.job_lembrete, time=dtime(12, 0, tzinfo=config.TZ))
    # morning flush: drena mensagens enfileiradas durante quiet hours
    jq.run_daily(handlers.job_morning_flush, time=dtime(8, 0, tzinfo=config.TZ))
    return app


def main() -> None:
    app = build_app()
    log.info("Starting long polling")
    app.run_polling(allowed_updates=["message", "callback_query"], drop_pending_updates=True)


if __name__ == "__main__":
    main()
