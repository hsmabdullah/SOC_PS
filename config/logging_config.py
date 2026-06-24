"""
config/logging_config.py
─────────────────────────
Centralised logging configuration for the SOC Triage Platform.

Design decisions:
    - Structured log format includes timestamp, level, module, and message
      so logs can be parsed by a SIEM or log-aggregation system.
    - Rotating file handler prevents unbounded disk growth.
    - Console handler uses a more readable short format for developer UX.
    - All platform modules call get_logger(___name___) — never print().
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


_LOG_FORMAT_FILE = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
)
_LOG_FORMAT_CONSOLE = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def configure_logging(log_level: str = "INFO", log_file: str = "logs/soc_triage.log") -> None:
    """
    Configure root logger with rotating file + console handlers.

    Args:
        log_level: One of DEBUG, INFO, WARNING, ERROR, CRITICAL.
        log_file:  Path to the rotating log file.

    This is idempotent — safe to call multiple times.
    """
    global _configured
    if _configured:
        return

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # ── File handler (10 MB per file, keep 5 backups) ────────────────────────
    file_handler = RotatingFileHandler(
        filename=str(log_path),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT_FILE, datefmt=_DATE_FORMAT))
    root.addHandler(file_handler)

    # ── Console handler ───────────────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(_LOG_FORMAT_CONSOLE, datefmt=_DATE_FORMAT))
    root.addHandler(console_handler)

    # Suppress noisy third-party loggers
    for noisy in ("urllib3", "httpx", "openai", "langchain", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.  Modules call this instead of logging.getLogger()
    directly so that logging is guaranteed to be configured.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        Configured Logger instance.
    """
    from config.settings import get_settings  # deferred to avoid circular import

    try:
        cfg = get_settings()
        configure_logging(cfg.app.log_level, cfg.app.log_file)
    except Exception:
        configure_logging()  # fallback defaults

    return logging.getLogger(name)