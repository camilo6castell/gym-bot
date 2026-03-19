from playwright.sync_api import Page, TimeoutError
from utils.logger import logger
from utils.human_behavior import human_delay
from utils.page_utils import wait_idle_and_search_selector


def gym_class_confirmation(page: Page):
    logger.info("🕤 Esperando modal de confirmación...")

    try:
        wait_idle_and_search_selector(page, "#btnConfirmarReserva", timeout=15000)
        human_delay()
        page.click("#btnConfirmarReserva")

    except TimeoutError:
        raise RuntimeError("❌ No apareció el botón Confirmar Reserva")
