"""Tests for Quiet Hours feature (e05).

Covers:
- is_quiet_hours() boundary conditions
- job_morning_flush drains the queue at 08:00
- manual=True bypasses the quiet-hours gate (_publicar_resultado)
- automatic path enqueues instead of sending during quiet hours
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from bolao import config
from bolao.handlers import _publicar_resultado, job_morning_flush
from bolao.util import is_quiet_hours


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_context(bot_data: dict | None = None) -> MagicMock:
    """Build a minimal fake context with an AsyncMock bot."""
    ctx = MagicMock()
    ctx.bot = AsyncMock()
    ctx.bot_data = bot_data if bot_data is not None else {}
    return ctx


def _make_db_stub() -> MagicMock:
    """Minimal async DB stub whose get_palpites() returns []."""
    stub = MagicMock()
    stub.get_palpites = AsyncMock(return_value=[])
    return stub


def _make_context_with_db(monkeypatch, grupo_chat_id: int) -> MagicMock:
    monkeypatch.setattr(config, "GRUPO_CHAT_ID", grupo_chat_id)
    ctx = _make_context()
    ctx.bot_data["pending_results"] = []
    # handlers.db(context) reads context.application.bot_data["db"]
    ctx.application = MagicMock()
    ctx.application.bot_data = {"db": _make_db_stub()}
    return ctx


JOGO = {
    "match_id": "R2-05",
    "casa": "Brasil",
    "fora": "Argentina",
    "gols_casa": 2,
    "gols_fora": 1,
    "status": "encerrado",
}


# ---------------------------------------------------------------------------
# Tests: is_quiet_hours()
# ---------------------------------------------------------------------------

class TestIsQuietHours:
    """is_quiet_hours() with explicit ref datetimes."""

    def _dt(self, hour: int, minute: int = 0) -> datetime:
        return datetime(2026, 6, 21, hour, minute, tzinfo=config.TZ)

    def test_21_59_not_quiet(self):
        assert is_quiet_hours(self._dt(21, 59)) is False

    def test_22_00_quiet(self):
        assert is_quiet_hours(self._dt(22, 0)) is True

    def test_midnight_quiet(self):
        assert is_quiet_hours(self._dt(0, 0)) is True

    def test_03_00_quiet(self):
        assert is_quiet_hours(self._dt(3, 0)) is True

    def test_07_59_quiet(self):
        assert is_quiet_hours(self._dt(7, 59)) is True

    def test_08_00_not_quiet(self):
        assert is_quiet_hours(self._dt(8, 0)) is False

    def test_12_00_not_quiet(self):
        assert is_quiet_hours(self._dt(12, 0)) is False


# ---------------------------------------------------------------------------
# Tests: job_morning_flush
# ---------------------------------------------------------------------------

class TestMorningFlush:
    """job_morning_flush drains pending_results queue and clears it."""

    async def test_sends_all_queued_and_clears(self, monkeypatch):
        monkeypatch.setattr(config, "GRUPO_CHAT_ID", -100123)
        items = [
            {"texto": "a", "parse_mode": "HTML"},
            {"texto": "b", "parse_mode": "HTML"},
        ]
        ctx = _make_context({"pending_results": list(items)})

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await job_morning_flush(ctx)

        assert ctx.bot.send_message.call_count == 2
        assert ctx.bot_data["pending_results"] == []

    async def test_empty_queue_does_nothing(self, monkeypatch):
        monkeypatch.setattr(config, "GRUPO_CHAT_ID", -100123)
        ctx = _make_context({"pending_results": []})

        await job_morning_flush(ctx)

        ctx.bot.send_message.assert_not_called()
        assert ctx.bot_data["pending_results"] == []

    async def test_no_grupo_chat_id_skips(self, monkeypatch):
        monkeypatch.setattr(config, "GRUPO_CHAT_ID", 0)
        ctx = _make_context({"pending_results": [{"texto": "x", "parse_mode": "HTML"}]})

        await job_morning_flush(ctx)

        ctx.bot.send_message.assert_not_called()
        assert ctx.bot_data["pending_results"] == []


# ---------------------------------------------------------------------------
# Tests: _publicar_resultado gating
# ---------------------------------------------------------------------------

class TestManualBypass:
    """manual=True sends immediately even during quiet hours."""

    async def test_manual_sends_despite_quiet_hours(self, monkeypatch):
        ctx = _make_context_with_db(monkeypatch, -100123)

        with patch("bolao.handlers.is_quiet_hours", return_value=True):
            await _publicar_resultado(ctx, JOGO, manual=True)

        ctx.bot.send_message.assert_called_once()
        assert ctx.bot_data["pending_results"] == []


class TestAutoEnqueues:
    """Automatic path (manual=False) enqueues during quiet hours."""

    async def test_auto_enqueues_not_sends(self, monkeypatch):
        ctx = _make_context_with_db(monkeypatch, -100123)

        with patch("bolao.handlers.is_quiet_hours", return_value=True):
            await _publicar_resultado(ctx, JOGO, manual=False)

        ctx.bot.send_message.assert_not_called()
        assert len(ctx.bot_data["pending_results"]) == 1

    async def test_auto_logs_enqueue(self, monkeypatch, caplog):
        ctx = _make_context_with_db(monkeypatch, -100123)
        caplog.set_level("INFO")

        with patch("bolao.handlers.is_quiet_hours", return_value=True):
            await _publicar_resultado(ctx, JOGO, manual=False)

        assert any("enfileirada" in msg for msg in caplog.messages)

    async def test_auto_sends_outside_quiet_hours(self, monkeypatch):
        ctx = _make_context_with_db(monkeypatch, -100123)

        with patch("bolao.handlers.is_quiet_hours", return_value=False):
            await _publicar_resultado(ctx, JOGO, manual=False)

        ctx.bot.send_message.assert_called_once()
        assert ctx.bot_data["pending_results"] == []
