"""Big Bolão — BigBase entry point: serves web/dist/ via HTTP + runs the bot."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
log = logging.getLogger("bolao.app")

# Load env
from dotenv import load_dotenv
BOLAO_ENV = Path("/opt/bolao/.env")
LOCAL_ENV = Path(__file__).resolve().parent / ".env"

if BOLAO_ENV.exists():
    load_dotenv(dotenv_path=str(BOLAO_ENV), override=True)
elif LOCAL_ENV.exists():
    load_dotenv(dotenv_path=str(LOCAL_ENV), override=True)
else:
    load_dotenv(override=True)

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Start Telegram bot in background thread
def run_bot():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        from bolao.config import validate_config, TELEGRAM_TOKEN
        validate_config()
        log.info("Bot starting with token %s…", TELEGRAM_TOKEN[:8] + "...")
        from bolao.bot import build_app
        bot_app = build_app()
        # stop_signals=[] evita set_wakeup_fd (so funciona na main thread)
        # Retry loop: durante deploy, a instancia antiga ainda segura o token.
        # Esperamos com backoff (5s, 10s, 15s…) ate a antiga ser desligada.
        from telegram.error import Conflict
        max_retries = 12
        for attempt in range(max_retries):
            try:
                bot_app.run_polling(
                    allowed_updates=["message", "callback_query"],
                    stop_signals=[],
                )
                break  # sucesso
            except Conflict:
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 5
                    log.info("Bot conflict (old instance still alive), retry in %ds… (%d/%d)",
                             wait, attempt + 1, max_retries)
                    time.sleep(wait)
                else:
                    raise
    except Exception as e:
        log.error("Bot failed: %s", e)

threading.Thread(target=run_bot, daemon=True).start()

# Get version from git
def get_version():
    try:
        short_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'],
                                            cwd=Path(__file__).resolve().parent,
                                            text=True).strip()
        return short_hash
    except Exception:
        return 'unknown'

# Serve web/dist/ as SPA on $PORT (BigBase health-checks this)
import http.server, socketserver

PORT = int(os.environ.get('PORT', 3000))
DIST = Path(__file__).resolve().parent / 'web' / 'dist'
VERSION = get_version()
log.info("Serving %s on :%d (version %s)", DIST, PORT, VERSION)


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def do_GET(self):
        path = self.path.split('?')[0].lstrip('/')

        # SPA: serve files or fallback to index.html
        full = DIST / path
        if not full.exists() or full.is_dir():
            self.path = '/index.html'
        super().do_GET()

    def log_message(self, fmt, *args):
        pass


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('0.0.0.0', PORT), SPAHandler) as httpd:
    log.info("HTTP server ready on :%d", PORT)
    httpd.serve_forever()
