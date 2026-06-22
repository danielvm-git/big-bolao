"""Big Bolão — BigBase entry point: serves web/dist/ via HTTP + runs the bot."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import threading
import time
from pathlib import Path

from bolao.logger import setup_logging, get_logger

setup_logging()
log = get_logger("bolao.app")

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

# ── New Relic APM (conditional) ──────────────────────────────
NEW_RELIC_LICENSE_KEY = os.environ.get("NEW_RELIC_LICENSE_KEY", "")
NEW_RELIC_APP_NAME = os.environ.get("NEW_RELIC_APP_NAME", "Big Bolao")
if NEW_RELIC_LICENSE_KEY:
    try:
        import newrelic.agent
        newrelic.agent.initialize(
            config_file=None,
            env="production",
        )
        log.info("New Relic APM initialized", extra={
            "app_name": NEW_RELIC_APP_NAME,
        })
    except Exception as exc:
        log.warning("New Relic APM init failed", extra={"error": str(exc)})
else:
    log.debug("New Relic APM not configured (set NEW_RELIC_LICENSE_KEY to enable)")

# Start Telegram bot in background thread
def run_bot():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        from bolao.config import validate_config, TELEGRAM_TOKEN
        validate_config()
        log.info("Starting bot", extra={
    "token_prefix": TELEGRAM_TOKEN[:8] + "...",
    "provider": "apifootball",
})
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

# Serve web/dist/ as SPA on $PORT (BigBase health-checks this).
# Version is baked into the JS bundle at build time (see web/vite.config.js) —
# BigBase's CSP `default-src 'self'` blocks inline scripts and intercepts
# /api/* routes, so a runtime version endpoint here would never reach the front.
import http.server, socketserver

PORT = int(os.environ.get('PORT', 3000))
DIST = Path(__file__).resolve().parent / 'web' / 'dist'
log.info("Serving web SPA", extra={"port": PORT, "dist": str(DIST)})


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def do_GET(self):
        path = self.path.split('?')[0].lstrip('/')
        ua = self.headers.get('User-Agent', '')

        # Health check — BigBase uses /health to verify the service is alive
        if path == 'health':
            from bolao.util import version
            self._send_json({"status": "ok", "service": "bolao", "version": version()})
            return

        # Telegram Instant View bot — serve static HTML for IV parser
        if path == '' and ('TelegramBot' in ua or 'TelegramIV' in ua):
            self._serve_telegram_iv()
            return

        # SPA: serve files or fallback to index.html
        full = DIST / path
        if not full.exists() or full.is_dir():
            self.path = '/index.html'
        super().do_GET()

    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_telegram_iv(self):
        """Serve static HTML page optimized for Telegram Instant View parser."""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(TELEGRAM_IV_HTML)))
        self.end_headers()
        self.wfile.write(TELEGRAM_IV_HTML.encode('utf-8'))

    def log_message(self, fmt, *args):
        # Structured JSON logging for every HTTP request
        status = args[0] if args else "?"
        log.info("HTTP %s %s → %s", self.command, self.path, status,
                 extra={
                     "http_method": self.command,
                     "http_path": self.path,
                     "http_status": int(status) if status.isdigit() else status,
                     "remote_ip": self.client_address[0],
                 })


TELEGRAM_IV_HTML = (
    '<!DOCTYPE html>\n'
    '<html lang="pt-BR">\n'
    '<head>\n'
    '<meta charset="UTF-8">\n'
    '<meta property="og:title" content="Big Bol&#227;o — Copa do Mundo 2026">\n'
    '<meta property="og:description" content="O bol&#227;o dos Jararacas. '
    'Palpite, ranking e resultados em tempo real.">\n'
    '<meta property="og:image" content="https://bolao.bigbase.click/og-image.png">\n'
    '<title>Big Bol&#227;o — Copa 2026</title>\n'
    '</head>\n'
    '<body>\n'
    '<article>\n'
    '<h1>Big Bol&#227;o — Copa do Mundo 2026</h1>\n'
    '<p>O bol&#227;o dos Jararacas. 72 jogos, 1 campe&#227;o.</p>\n'
    '<p>Palpite no placar exato dos jogos, acompanhe o ranking ao vivo '
    'e veja os resultados.</p>\n'
    '<p><b>Pontua&#231;&#227;o:</b> 3 pontos por placar exato, '
    '1 ponto por acertar o vencedor.</p>\n'
    '<p><a href="https://bolao.bigbase.click/">Acessar o bol&#227;o</a></p>\n'
    '<p><a href="https://t.me/JararacasBolao_bot">Falar com o bot no '
    'Telegram</a></p>\n'
    '</article>\n'
    '</body>\n'
    '</html>'
)


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('0.0.0.0', PORT), SPAHandler) as httpd:
    log.info("HTTP server ready", extra={"port": PORT, "dist": str(DIST)})
    httpd.serve_forever()
