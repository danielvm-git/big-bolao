"""Structured JSON logging for the bolao project.

Usage:
    from bolao.logger import setup_logging, get_logger

    setup_logging()
    log = get_logger(__name__)

    log.info("User action", extra={"user_id": 12345, "action": "palpite"})
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """Produces structured JSON log entries.

    Format:
    {"level":"INFO","timestamp":"2026-06-21T13:45:23.123+00:00",
     "logger":"bolao.bigbase","message":"create participante",
     "user_id":12345,"duration_ms":42}
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "level": record.levelname,
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Merge extra context fields passed via extra={...}
        # Skip stdlib keys to avoid cluttering the JSON
        skip = {
            "args", "asctime", "created", "exc_info", "exc_text",
            "filename", "funcName", "levelname", "levelno", "lineno",
            "message", "module", "msecs", "msg", "name", "pathname",
            "process", "processName", "relativeCreated", "stack_info",
            "taskName", "thread", "threadName",
        }
        for key, value in record.__dict__.items():
            if key not in skip:
                log_entry[key] = value

        return json.dumps(log_entry, ensure_ascii=False, default=str)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with JSON output to stdout.

    Call once at process startup (in app.py or bot.py main).
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    # force=True replaces any previous basicConfig configuration
    logging.basicConfig(level=level, handlers=[handler], force=True)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given module name.

    Shorthand for logging.getLogger(name).
    """
    return logging.getLogger(name)
