"""Big Bolão — serves Vue SPA + proxies /api to BigBase + runs the Telegram bot.

Deployed via BigBase, which runs `python app.py` with PORT env var set.
Uses only stdlib + httpx (already in requirements.txt). No Flask/FastAPI.
"""
from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
import os
import sys
import threading
from pathlib import Path

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
log = logging.getLogger("bolao.app")

PORT = int(os.environ.get("PORT", "8080"))
BIGBASE_URL = os.environ.get("BIGBASE_URL", "https://bigbase.click")
STATIC_DIR = Path(__file__).resolve().parent / "web" / "dist"

mimetypes.init()


async def handle_request(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Handle a single HTTP request."""
    try:
        request_line = await asyncio.wait_for(reader.readline(), timeout=10)
        if not request_line:
            return
        parts = request_line.decode("utf-8", errors="replace").strip().split()
        if len(parts) < 2:
            return
        method = parts[0]
        path = parts[1]

        # Read headers
        headers = {}
        while True:
            line = await asyncio.wait_for(reader.readline(), timeout=10)
            if line in (b"\r\n", b"\n", b""):
                break
            decoded = line.decode("utf-8", errors="replace").strip()
            if ":" in decoded:
                k, v = decoded.split(":", 1)
                headers[k.strip().lower()] = v.strip()

        # Read body if present
        content_length = int(headers.get("content-length", 0))
        body = b""
        if content_length > 0:
            body = await asyncio.wait_for(reader.readexactly(content_length), timeout=30)

        # Route
        if path.startswith("/api/"):
            await proxy_request(method, path, headers, body, writer)
        else:
            await serve_static(path, method, writer)
    except asyncio.TimeoutError:
        pass
    except Exception as e:
        log.error("request error: %s", e, exc_info=True)
    finally:
        try:
            writer.close()
        except Exception:
            pass


async def proxy_request(method: str, path: str, headers: dict, body: bytes,
                        writer: asyncio.StreamWriter):
    """Proxy /api/* requests to BigBase."""
    query = ""
    if "?" in path:
        path, query = path.split("?", 1)

    target_url = f"{BIGBASE_URL}{path}"
    if query:
        target_url += f"?{query}"

    # Forward auth/content-type headers
    fwd_headers = {}
    for key in ("content-type", "authorization"):
        if key in headers:
            fwd_headers[key] = headers[key]

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.request(
                method,
                target_url,
                content=body if method in ("POST", "PUT", "PATCH") else None,
                headers=fwd_headers,
            )
    except Exception as e:
        log.error("proxy error %s: %s", path, e)
        await send_json(writer, 502, {"error": f"proxy error: {e}"})
        return

    # Forward response
    ct = resp.headers.get("content-type", "application/json")
    await send_raw(writer, resp.status_code, ct, resp.content)


async def serve_static(path: str, method: str, writer: asyncio.StreamWriter):
    """Serve files from web/dist/."""
    if method != "GET":
        await send_json(writer, 405, {"error": "method not allowed"})
        return

    # SPA: all non-asset routes serve index.html
    if path == "/" or not path.startswith("/assets/"):
        file_path = STATIC_DIR / "index.html"
    else:
        file_path = STATIC_DIR / path.lstrip("/")

    if not file_path.exists() or not file_path.is_file():
        file_path = STATIC_DIR / "index.html"

    content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    try:
        content = file_path.read_bytes()
    except Exception:
        await send_json(writer, 404, {"error": "not found"})
        return

    cache = "public, max-age=31536000, immutable" if "/assets/" in path else "no-cache"
    header_lines = (
        f"HTTP/1.1 200 OK\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(content)}\r\n"
        f"Cache-Control: {cache}\r\n"
        f"Access-Control-Allow-Origin: *\r\n"
        f"\r\n"
    ).encode()
    writer.write(header_lines + content)
    await writer.drain()


async def send_json(writer: asyncio.StreamWriter, status: int, data: dict):
    body = json.dumps(data).encode()
    header_lines = (
        f"HTTP/1.1 {status} {'OK' if status == 200 else 'Error'}\r\n"
        f"Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Access-Control-Allow-Origin: *\r\n"
        f"\r\n"
    ).encode()
    writer.write(header_lines + body)
    await writer.drain()


async def send_raw(writer: asyncio.StreamWriter, status: int,
                   content_type: str, body: bytes):
    header_lines = (
        f"HTTP/1.1 {status} {'OK' if status < 400 else 'Error'}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Access-Control-Allow-Origin: *\r\n"
        f"\r\n"
    ).encode()
    writer.write(header_lines + body)
    await writer.drain()


def run_bot_sync():
    """Run the Telegram bot in a separate thread (sync wrapper)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from dotenv import load_dotenv
    load_dotenv(override=True)
    from bolao.config import validate_config
    try:
        validate_config()
    except RuntimeError as e:
        log.warning("Config validation: %s", e)
    from bolao.bot import build_app
    app_bot = build_app()
    log.info("Bot iniciando (long polling)...")
    app_bot.run_polling(allowed_updates=["message", "callback_query"])


async def main():
    # Start bot in thread
    bot_thread = threading.Thread(target=run_bot_sync, daemon=True)
    bot_thread.start()
    log.info("Bot thread started")

    # Start web server
    server = await asyncio.start_server(handle_request, "0.0.0.0", PORT)
    addr = server.sockets[0].getsockname()
    log.info("Web server rodando em http://0.0.0.0:%d (PID %d)", addr[1], os.getpid())

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
