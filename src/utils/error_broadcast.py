"""Error broadcast: notify via Telegram and save diagnostic screenshot."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

from src.types.browser import IPage
from src.utils.logger import logger

if TYPE_CHECKING:
    from src.notifications import Notifier

_DEBUG_DIR = Path(__file__).resolve().parent.parent.parent / "debug"


class ErrorBroadcaster:
    """
    Notify critical errors and save a diagnostic screenshot locally.

    The notifier is injected via constructor (dependency inversion),
    making it testable with a fake implementation.
    """

    def __init__(self, notifier: Notifier, debug_dir: Path = _DEBUG_DIR) -> None:
        self._notifier = notifier
        self._debug_dir = debug_dir
        self._debug_dir.mkdir(exist_ok=True)

    def send(self, page: IPage, error_message: str) -> None:
        """Notify the error and save a best-effort page screenshot."""
        self._notifier.notify(f"❌ → {error_message}")
        logger.error(f"❌ → {error_message}")

        screenshot_path = self._debug_dir / f"error_{int(time.time())}.png"
        try:
            page.screenshot(path=str(screenshot_path))
            logger.debug(f"📸 → Screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.debug(f"📸 → Could not save screenshot: {e}")
