"""Centralized logging configuration for AI-Kaizen.

Usage:
    from ai_kaizen.logging_config import setup_logging
    setup_logging()                        # human-readable, INFO level
    setup_logging(level="DEBUG")           # verbose
    setup_logging(json_format=True)        # structured JSON (for log aggregators)

Environment variables:
    AI_KAIZEN_LOG_LEVEL  — override log level (DEBUG, INFO, WARNING, ERROR)
    AI_KAIZEN_LOG_JSON   — set to "1" for JSON output
"""

from __future__ import annotations

import json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

# Request ID for correlating web request logs
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

_CONFIGURED = False


class _JsonFormatter(logging.Formatter):
    """Structured JSON log lines — one object per line."""

    def format(self, record: logging.LogRecord) -> str:
        obj = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id_var.get("-"),
        }
        if record.exc_info and record.exc_info[0]:
            obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(obj, default=str)


class _HumanFormatter(logging.Formatter):
    """Coloured, human-readable log output for terminals."""

    COLORS = {
        "DEBUG": "\033[90m",     # grey
        "INFO": "\033[36m",      # cyan
        "WARNING": "\033[33m",   # yellow
        "ERROR": "\033[31m",     # red
        "CRITICAL": "\033[1;31m",  # bold red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        rid = request_id_var.get("-")
        prefix = f"[{rid[:8]}] " if rid != "-" else ""
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        base = f"{color}{ts} {record.levelname:<7}{self.RESET} {prefix}{record.name}: {record.getMessage()}"
        if record.exc_info and record.exc_info[0]:
            base += "\n" + self.formatException(record.exc_info)
        return base


def setup_logging(
    level: str | None = None,
    json_format: bool | None = None,
) -> None:
    """Configure logging for the entire application. Safe to call multiple times."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True

    level = level or os.environ.get("AI_KAIZEN_LOG_LEVEL", "INFO")
    if json_format is None:
        json_format = os.environ.get("AI_KAIZEN_LOG_JSON", "0") == "1"

    root = logging.getLogger("ai_kaizen")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_JsonFormatter() if json_format else _HumanFormatter())
    root.addHandler(handler)

    # Suppress noisy library loggers
    for name in ("urllib3", "werkzeug"):
        logging.getLogger(name).setLevel(logging.WARNING)
