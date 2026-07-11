"""Confirmación de la reserva en el modal de la plataforma."""

from __future__ import annotations

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from src.utils.exceptions import ElementNotFoundError
from src.utils.human_behavior import human_delay
from src.utils.logger import logger
from src.utils.recovery import Recovery


class ClassAcceptance:
    """Confirma la reserva de una clase en el modal de confirmación."""

    def __init__(self, recovery: Recovery) -> None:
        self._recovery = recovery

    def confirm(self, page: Page) -> None:
        """Espera el modal de confirmación, hace clic en 'Confirmar' y cierra el aviso."""
        logger.info("🕤 → Esperando modal de confirmación...")
        human_delay()

        confirm_selector = (
            "#btnConfirmarReserva:not([disabled])"
            if page.query_selector("#btnConfirmarReserva")
            else "button:has-text('Confirmar'):not([disabled])"
        )

        try:
            page.wait_for_selector(confirm_selector, state="visible", timeout=15000)
        except PlaywrightTimeoutError as err:
            raise ElementNotFoundError("❌ → No apareció el botón Confirmar Reserva") from err

        human_delay(0.5, 1.0)

        self._recovery.with_soft_recovery(
            lambda: page.click(confirm_selector),
            page,
            "Clickeando botón Confirmar Reserva",
        )

        human_delay()

        self._recovery.with_soft_recovery(
            lambda: self._close_notific8(page),
            page,
            "Cerrando notificación de éxito",
        )

        logger.success("✔️ → Ciclo de reserva hecho.")

    def _close_notific8(self, page: Page, timeout: int = 5000) -> None:
        """Cierra notificación notific8 haciendo hover para revelar el botón de cierre."""
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
                logger.info("😉 → Notificación de reserva cerrada.")
        except PlaywrightTimeoutError:
            logger.debug("🗑️ → Notificación no apareció o ya se cerró sola.")
