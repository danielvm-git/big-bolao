"""Tests for the /version diagnostic — version() accessor + cmd_version handler.

A /version command lets an operator see which build answered a command, so a
stale (zombie) bot instance long-polling the same token is immediately visible.
"""
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from bolao import handlers
from bolao.util import version


def test_version_matches_version_file():
    """version() returns the trimmed contents of the repo-root VERSION file."""
    expected = (Path(__file__).resolve().parent.parent / "VERSION").read_text(
        encoding="utf-8").strip()
    assert version() == expected


def test_version_is_nonempty_semver_like():
    """The running version is a real release string, not empty/unknown."""
    v = version()
    assert v not in ("", "desconhecida")
    assert v[0].isdigit()  # e.g. "1.11.0"


@pytest.mark.asyncio
async def test_cmd_version_replies_with_running_version():
    """/version replies with text containing the current build version."""
    update = AsyncMock()
    await handlers.cmd_version(update, AsyncMock())
    update.message.reply_text.assert_awaited_once()
    sent = update.message.reply_text.await_args.args[0]
    assert version() in sent
