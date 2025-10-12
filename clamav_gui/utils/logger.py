"""
Application logging utilities.
Provides daily rotating file logs under the project-level 'logs/' directory
and stdout streaming. Call configure_logging() once at startup.
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import List

_LOG_CONFIGURED = False


def _project_root() -> Path:
    """Best-effort project root directory (the clamav-gui repo root).

    Expected path layout: <repo>/clamav_gui/utils/logger.py
    So repo root is typically `here.parents[2]`.
    We also probe upwards for a marker ('.git' or 'README.md') as a sanity check.
    Fallback to current working directory on failure.
    """
    here = Path(__file__).resolve()
    # Prefer the directory two levels up: .../clamav-gui
    candidates = []
    try:
        candidates.append(here.parents[2])  # repo root
    except Exception:
        pass
    # Probe additional parents just in case
    candidates.extend(list(here.parents[3:6]))
    for cand in candidates:
        if not isinstance(cand, Path):
            continue
        try:
            if (cand / '.git').exists() or (cand / 'README.md').exists() or (cand / 'clamav_gui').exists():
                return cand
        except Exception:
            continue
    # Fallback to two levels up if available
    try:
        return here.parents[2]
    except Exception:
        # Last resort: current working directory
        return Path.cwd()


def ensure_logs_dir() -> Path:
    """Ensure logs directory exists at project root, return its path."""
    logs_dir = _project_root() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def _build_file_handler(level: int) -> TimedRotatingFileHandler:
    logs_dir = ensure_logs_dir()
    log_file = logs_dir / "app.log"
    handler = TimedRotatingFileHandler(
        filename=str(log_file), when="midnight", interval=1, backupCount=14, encoding="utf-8"
    )
    handler.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    return handler


def _build_stream_handler(level: int) -> logging.Handler:
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    return handler


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging with stdout + daily rotating file handler.

    Idempotent: safe to call multiple times.
    """
    global _LOG_CONFIGURED
    if _LOG_CONFIGURED:
        return

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicating handlers if environment already configured
    if not any(isinstance(h, TimedRotatingFileHandler) for h in root.handlers):
        root.addHandler(_build_file_handler(level))
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(_build_stream_handler(level))

    _LOG_CONFIGURED = True


def get_logger(name: str = "ClamAV-GUI") -> logging.Logger:
    """Get a named logger after ensuring logging is configured."""
    configure_logging()
    logger = logging.getLogger(name)
    logger.propagate = True
    return logger


def get_log_files() -> List[Path]:
    """Return list of log files sorted by modified time descending."""
    logs_dir = ensure_logs_dir()
    files = list(logs_dir.glob("app.log*"))
    files.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    return files
