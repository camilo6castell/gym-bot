from playwright.sync_api import Page, TimeoutError
from utils.human_behavior import human_delay
from utils.logger import logger
from utils.page_utils import dismiss_if_present, search_and_click
from utils.recovery import with_soft_recovery


def gym_class_confirmation(page: Page):
    logger.info("🕤 → Esperando modal de confirmación...")
    human_delay()
    try:

        with_soft_recovery(
            lambda: dismiss_if_present(page, "#btnConfirmarReserva", True, 15000),
            page,
            "Confirmando modal de reserva de clase",
        )
        human_delay()
        with_soft_recovery(
            lambda: dismiss_if_present(page, ".notific8-close-button", False, 15000),
            page,
            "Cerrando notificación de éxito de reserva",
        )
        logger.success("✔️  → Ciclo de reserva hecho, esperando confirmación final.")
    except TimeoutError:
        raise RuntimeError("❌ → No apareció el botón Confirmar Reserva")
