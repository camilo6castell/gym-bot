"""Difusión de errores: notifica por Telegram y guarda evidencia (screenshot)."""

from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import Page

from src.notifications.telegram import TelegramClient
from src.utils.logger import logger

_DEBUG_DIR = Path(__file__).resolve().parent.parent.parent / "debug"


class ErrorBroadcaster:
    """
    Notifica errores críticos por Telegram y adjunta un screenshot de
    diagnóstico, guardado localmente en el directorio `debug/`.
    """

    def __init__(self, notifier: TelegramClient, debug_dir: Path = _DEBUG_DIR) -> None:
        """
        Parameters
        ----------
        notifier : TelegramClient
            Cliente usado para notificar el error.
        debug_dir : Path
            Directorio donde se guardan los screenshots de diagnóstico.
        """
        self._notifier = notifier
        self._debug_dir = debug_dir
        self._debug_dir.mkdir(exist_ok=True)

    def send(self, page: Page, error_message: str) -> None:
        """Notifica el error y adjunta un screenshot best-effort de la página."""
        self._notifier.notify(f"❌ → {error_message}")
        logger.error(f"❌ → {error_message}")

        screenshot_path = self._debug_dir / f"error_{int(time.time())}.png"
        try:
            page.screenshot(path=str(screenshot_path))
            logger.debug(f"📸 → Screenshot guardado: {screenshot_path}")
        except Exception as e:
            logger.debug(f"📸 → No se pudo guardar screenshot: {e}")
