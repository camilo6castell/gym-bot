from playwright.sync_api import Page, TimeoutError
from src.utils.human_behavior import human_delay
from src.utils.logger import logger
from src.utils.recovery import recovery


def perform_gym_class_acceptance(page: Page) -> None:
    logger.info("🕤 → Esperando modal de confirmación...")
    human_delay()

    confirm_selector = (
        "#btnConfirmarReserva:not([disabled])"
        if page.query_selector("#btnConfirmarReserva")
        else "button:has-text('Confirmar'):not([disabled])"
    )

    try:
        page.wait_for_selector(confirm_selector, state="visible", timeout=15000)
    except TimeoutError:
        raise RuntimeError("❌ → No apareció el botón Confirmar Reserva")

    human_delay(0.5, 1.0)

    recovery.with_soft_recovery(
        lambda: page.click(confirm_selector),
        page,
        "Clickeando botón Confirmar Reserva",
    )

    human_delay()

    recovery.with_soft_recovery(
        lambda: _close_notific8(page),
        page,
        "Cerrando notificación de éxito",
    )

    logger.success("✔️ → Ciclo de reserva hecho.")


def _close_notific8(page: Page, timeout: int = 5000) -> None:
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
    except TimeoutError:
        logger.debug("🗑️ → Notificación no apareció o ya se cerró sola.")
