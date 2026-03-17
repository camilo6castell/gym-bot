from playwright.sync_api import Page, TimeoutError
from utils.logger import logger
from utils.human_behavior import human_delay


def gym_class_confirmation(page: Page):
    logger.info("Esperando modal de confirmación...")

    try:
        page.wait_for_selector("#btnConfirmarReserva", timeout=15000)

        human_delay()
        page.click("#btnConfirmarReserva")

        logger.success("Reserva confirmada")

    except TimeoutError:
        raise RuntimeError("No apareció el botón Confirmar Reserva")
