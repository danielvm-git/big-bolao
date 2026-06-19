"""Big Bolão — entry point for BigBase deploy: only runs the Telegram bot.

Static files (Vue SPA) are served by Caddy. API calls are proxied to BigBase
by Caddy. The bot runs long-polling in this process.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
log = logging.getLogger("bolao.app")

# Load .env if present (not in git, added by setup_server.sh)
from dotenv import load_dotenv
load_dotenv(override=True)

# Load config — will fail with helpful error if env vars missing
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bolao.config import validate_config, TELEGRAM_TOKEN

try:
    validate_config()
except RuntimeError as e:
    log.warning("Config: %s", e)

log.info("Starting bot with TELEGRAM_TOKEN=%s…", TELEGRAM_TOKEN[:8] + "...")

from bolao.bot import build_app
app = build_app()
log.info("Bot iniciando (long polling)...")
app.run_polling(allowed_updates=["message", "callback_query"])
