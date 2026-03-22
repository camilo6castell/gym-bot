from playwright.sync_api import Page, TimeoutError
from utils.logger import logger
from utils.page_utils import dismiss_if_present, search_and_click
from utils.recovery import with_soft_recovery


def gym_class_confirmation(page: Page):
    logger.info("🕤 → Esperando modal de confirmación...")
    try:
        search_and_click(page, "#btnConfirmarReserva", timeout=5000)
    except TimeoutError:
        raise RuntimeError("❌ → No apareció el botón Confirmar Reserva")
