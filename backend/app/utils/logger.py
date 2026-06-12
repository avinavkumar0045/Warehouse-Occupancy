"""
Centralized logging configuration for the Warehouse Occupancy Platform.

Creates four rotating log files:
  - logs/application.log  — General app lifecycle and debug messages
  - logs/scheduler.log    — APScheduler job activity
  - logs/occupancy.log    — AI model output and estimation events
  - logs/camera.log       — RTSP connection and camera health checks

Usage:
    from app.utils.logger import get_logger
    logger = get_logger(__name__)
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────
LOG_DIR = Path(__file__).resolve().parents[3] / "logs"  # backend/logs/
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB per file
BACKUP_COUNT = 5               # keep up to 5 rotated files

# Channel → log-file mapping
_CHANNEL_FILES: dict[str, str] = {
    "scheduler": "scheduler.log",
    "occupancy": "occupancy.log",
    "camera":    "camera.log",
}
_DEFAULT_FILE = "application.log"


def _ensure_log_dir() -> None:
    """Create the logs/ directory if it does not exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _make_rotating_handler(filename: str) -> RotatingFileHandler:
    """Return a configured RotatingFileHandler for the given filename."""
    path = LOG_DIR / filename
    handler = RotatingFileHandler(
        path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    return handler


def _route_file(name: str) -> str:
    """
    Choose the log file based on the logger name.

    Heuristic: if any channel keyword appears in the dotted name, use that
    channel's file. Falls back to application.log.
    """
    lower = name.lower()
    for channel, filename in _CHANNEL_FILES.items():
        if channel in lower:
            return filename
    return _DEFAULT_FILE


def setup_logging() -> None:
    """
    Call once at application startup (from main.py) to configure the root
    logger with both a console handler and a per-channel rotating file handler.
    """
    _ensure_log_dir()

    # --- root logger ---
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Prevent double-adding handlers when uvicorn reloads
    if root.handlers:
        return

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(console)

    # One rotating handler per channel
    for filename in set(_CHANNEL_FILES.values()) | {_DEFAULT_FILE}:
        root.addHandler(_make_rotating_handler(filename))

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Return a module-level logger.  The logger automatically routes to the
    correct rotating log file based on the module name heuristic.

    Args:
        name: typically ``__name__`` of the calling module.

    Returns:
        A ``logging.Logger`` instance.
    """
    _ensure_log_dir()
    logger = logging.getLogger(name)

    # Attach a dedicated rotating file handler if the channel warrants it
    filename = _route_file(name)
    if filename != _DEFAULT_FILE:
        # Only attach if no file handler for this file exists yet
        existing_files = {
            getattr(h, "baseFilename", None)
            for h in logger.handlers
            if isinstance(h, RotatingFileHandler)
        }
        target_path = str(LOG_DIR / filename)
        if target_path not in existing_files:
            logger.addHandler(_make_rotating_handler(filename))

    return logger
