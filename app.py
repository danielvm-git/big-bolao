"""Big Bolão — BigBase entry point: serves web/dist/ via HTTP + runs the bot."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
import threading
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
        bot_app.run_polling(
            allowed_updates=["message", "callback_query"],
            stop_signals=[],
        )
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

# Simple sliding-window rate limiter for /api/version (max 30req/min)
_rate_limits: dict[str, list[float]] = {}
_RATE_LIMIT_MAX = 30
_RATE_LIMIT_WINDOW = 60.0


def _check_rate_limit(client_ip: str) -> bool:
    import time as _time
    now = _time.time()
    window_start = now - _RATE_LIMIT_WINDOW
    timestamps = [t for t in _rate_limits.get(client_ip, []) if t > window_start]
    _rate_limits[client_ip] = timestamps
    if len(timestamps) >= _RATE_LIMIT_MAX:
        return False
    timestamps.append(now)
    return True


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def do_GET(self):
        path = self.path.split('?')[0].lstrip('/')

        # API: return version (rate-limited)
        if path == 'api/version':
            client_ip = self.client_address[0]
            if not _check_rate_limit(client_ip):
                self.send_response(429)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'rate limit exceeded'}).encode())
                return
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'version': VERSION}).encode())
            return

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
