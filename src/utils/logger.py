"""
Logging configuration for gym-bot.

Two sinks on the same Loguru `logger`:

  - **stdout**: compact and colourised for interactive runs.
  - **file** (`logs/`): plain text (no colour codes), designed as a fast,
    `journalctl`-free view — `tail -f logs/<file>` shows lines in real
    time without the extra timestamp that journald prefixes.  The file is
    line-count-bounded (`LOG_MAX_LINES` env var): when exceeded, the oldest
    lines are dropped to make room for new ones (FIFO).

Design note: unlike the rest of the application (which receives config via
constructor), this module self-configures at import time — the same way
`logging.basicConfig` would.  It is cross-cutting infrastructure, not a
domain component, so it reads `.env` directly rather than depending on
`Settings` (which does not exist yet at the time this module is imported).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from loguru import logger

if TYPE_CHECKING:
    from loguru import Message

load_dotenv()

# ─── File sink configuration (via .env) ──────────────────────────────────────

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_LOG_DIR = _PROJECT_ROOT / os.getenv("LOG_DIR", "logs")
_LOG_FILENAME = os.getenv("LOG_FILENAME", "logger.txt")
_LOG_FILE = _LOG_DIR / _LOG_FILENAME
_LOG_MAX_LINES = int(os.getenv("LOG_MAX_LINES", "5000"))

_FILE_FORMAT = "{time:MM/DD HH:mm:ss} | {message}"

_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE.touch(exist_ok=True)


def _file_sink(message: Message) -> None:
    """
    File sink with line-count-based rotation.

    Appends the already-formatted Loguru line and, if the file exceeds
    `LOG_MAX_LINES`, trims it to keep only the most recent lines.
    """
    with open(_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(str(message))

    with open(_LOG_FILE, encoding="utf-8") as f:
        lines = f.readlines()

    if len(lines) > _LOG_MAX_LINES:
        with open(_LOG_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines[-_LOG_MAX_LINES:])


# ─── Logger config ───────────────────────────────────────────────────────────
logger.remove()

logger.add(
    sys.stdout,
    level="INFO",
    format=("<green>{time:MM/DD HH:mm:ss}</green> | {message}"),
)

logger.add(
    _file_sink,
    level="INFO",
    format=_FILE_FORMAT,
)
