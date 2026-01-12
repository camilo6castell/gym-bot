from playwright.sync_api import Page, TimeoutError
from loguru import logger
from bot.browser import human_delay


def confirmar_reserva(page: Page):
    logger.info("Esperando modal de confirmación...")

    try:
        page.wait_for_selector("#btnConfirmarReserva", timeout=15000)

        human_delay()
        page.click("#btnConfirmarReserva")

        logger.success("Reserva confirmada")

    except TimeoutError:
        raise RuntimeError("No apareció el botón Confirmar Reserva")
