"""Big Bolão — entry point for BigBase deploy: only runs the Telegram bot.

Static files (Vue SPA) are served by Caddy. API calls are proxied to BigBase
by Caddy. The bot runs long-polling in this process.

Env vars are loaded from (in order of precedence):
  1. /opt/bolao/.env          (production, BigBase deploy)
  2. .env in current dir      (local dev)
  3. shell environment        (fallback)
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

# Load project-specific .env (production path first, then local)
from dotenv import load_dotenv
BOLAO_ENV = Path("/opt/bolao/.env")
LOCAL_ENV = Path(__file__).resolve().parent / ".env"

if BOLAO_ENV.exists():
    load_dotenv(dotenv_path=str(BOLAO_ENV), override=True)
    log.info("Loaded env from %s", BOLAO_ENV)
elif LOCAL_ENV.exists():
    load_dotenv(dotenv_path=str(LOCAL_ENV), override=True)
    log.info("Loaded env from %s", LOCAL_ENV)
else:
    load_dotenv(override=True)  # try cwd .env as last resort
    log.info("No .env found — using shell env")

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
