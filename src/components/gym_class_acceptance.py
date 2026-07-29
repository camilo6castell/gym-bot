"""Reservation confirmation in the platform modal."""

from __future__ import annotations

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from src.utils.exceptions import ElementNotFoundError
from src.utils.human_behavior import human_delay
from src.utils.logger import logger
from src.utils.recovery import Recovery


class ClassAcceptance:
    """Confirm a class reservation inside the confirmation modal."""

    def __init__(self, recovery: Recovery) -> None:
        self._recovery = recovery

    def confirm(self, page: Page) -> None:
        """Wait for the confirmation modal, click 'Confirmar', and close the notification."""
        logger.info("🕤 → Waiting for confirmation modal...")
        human_delay()

        confirm_selector = (
            "#btnConfirmarReserva:not([disabled])"
            if page.query_selector("#btnConfirmarReserva")
            else "button:has-text('Confirmar'):not([disabled])"
        )

        try:
            page.wait_for_selector(confirm_selector, state="visible", timeout=15000)
        except PlaywrightTimeoutError as err:
            raise ElementNotFoundError("❌ → Confirm button did not appear") from err

        human_delay(0.5, 1.0)

        self._recovery.with_soft_recovery(
            lambda: page.click(confirm_selector),
            page,
            "Clicking Confirm Reserva button",
        )

        human_delay()

        self._recovery.with_soft_recovery(
            lambda: self._close_notific8(page),
            page,
            "Closing success notification",
        )

        logger.success("✔️ → Reservation cycle complete.")

    def _close_notific8(self, page: Page, timeout: int = 5000) -> None:
        """Close a notific8 notification by hovering to reveal the close button."""
        try:
            notification = page.wait_for_selector(
                "notific8-notification[open]", state="attached", timeout=timeout
            )
            if not notification:
                return
            notification.hover()
            human_delay(0.3, 0.6)
            close_btn = page.wait_for_selector(
                ".notific8-close-button", state="visible", timeout=3000
            )
            if close_btn:
                close_btn.click()
                logger.info("😉 → Reservation notification closed.")
        except PlaywrightTimeoutError:
            logger.debug("🗑️ → Notification did not appear or already closed.")
