from playwright.sync_api import Page
from utils.logger import logger
from utils.element_utils import str_normalizer
from utils.human_behavior import human_delay
from utils.days_handler import spanish_day_mapper


def select_latest_date(page: Page):
    logger.info("🕒 Seleccionando última fecha disponible...")

    page.wait_for_selector("button.botonfecha", timeout=15000)
    botones = page.query_selector_all("button.botonfecha")

    ultimo = botones[-1]
    human_delay()
    ultimo.click()

    logger.success("🕒 Última fecha seleccionada")


def select_by_day(page: Page, spanish_day_name: str):
    logger.info(f"🕒 Buscando fecha correspondiente a '{spanish_day_name}'")
    page.wait_for_selector("button.botonfecha", timeout=15000)

    botones = page.query_selector_all("button.botonfecha")

    for boton in botones:
        texto = str_normalizer(boton.inner_text())

        if spanish_day_name in texto:
            human_delay()
            boton.click()
            logger.success(f"🕒 Fecha seleccionada: {texto}")
            return

    logger.warning(f"⛔ No se encontró fecha para el día {spanish_day_name}")
