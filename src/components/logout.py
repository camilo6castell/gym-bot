"""Logout at the end of the reservation flow."""

from __future__ import annotations

from playwright.sync_api import Page

from src.utils.human_behavior import human_delay
from src.utils.logger import logger
from src.utils.page_utils import search_and_click, wait_network_idle
from src.utils.recovery import Recovery


class LogoutPage:
    """Log the user out at the end of the flow, best-effort without propagating errors."""

    def __init__(self, recovery: Recovery) -> None:
        self._recovery = recovery

    def perform_logout(self, page: Page) -> None:
        """Attempt to log out best-effort; never interrupts the main flow."""
        try:
            logger.info("🚪 → Attempting logout")
            human_delay()

            self._recovery.with_soft_recovery(
                lambda: search_and_click(page, "i.dropdown-icon", timeout=5000),
                page,
                "Waiting for user dropdown menu",
            )
            human_delay()

            self._recovery.with_soft_recovery(
                lambda: search_and_click(page, "a:has-text('Salir')", timeout=5000),
                page,
                "Attempting to click 'Salir'",
            )

            wait_network_idle(page, timeout=10000)
            logger.success("✅ → Session closed successfully")

        except Exception as e:
            logger.warning(f"⚠️ → Could not logout cleanly: {e}")
