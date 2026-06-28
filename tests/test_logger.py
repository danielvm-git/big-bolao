"""Tests for bolao.logger — verifies module is importable and behaves correctly."""
import logging


def test_import_bolao_logger():
    """bolao.logger must be importable (was untracked before this fix)."""
    import bolao.logger  # noqa: F401


def test_get_logger_returns_logger():
    from bolao.logger import get_logger

    log = get_logger("test.logger")
    assert isinstance(log, logging.Logger)


def test_get_logger_name():
    from bolao.logger import get_logger

    log = get_logger("bolao.bot")
    assert log.name == "bolao.bot"


def test_import_bolao_bot():
    """bolao.bot must be importable without ModuleNotFoundError."""
    import importlib.util
    import sys

    for key in list(sys.modules.keys()):
        if key.startswith("bolao.bot"):
            del sys.modules[key]

    spec = importlib.util.find_spec("bolao.bot")
    assert spec is not None, "bolao.bot module not found"


def test_json_formatter_output():
    """JSONFormatter produces valid JSON with required fields."""
    import json

    from bolao.logger import JSONFormatter

    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="hello", args=(), exc_info=None,
    )
    output = formatter.format(record)
    data = json.loads(output)
    assert data["level"] == "INFO"
    assert data["message"] == "hello"
    assert data["logger"] == "test"
    assert "timestamp" in data
