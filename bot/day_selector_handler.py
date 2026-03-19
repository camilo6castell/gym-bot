from playwright.sync_api import Page
from utils.logger import logger
from utils.element_utils import str_normalizer
from utils.human_behavior import human_delay
from utils.page_utils import wait_idle_and_search_selector


def collecting_avaible_date_buttons(page: Page):
    wait_idle_and_search_selector(page, "button.botonfecha", timeout=15000)
    return page.query_selector_all("button.botonfecha")


def select_latest_date(page: Page) -> bool:

    logger.info("🕒 Seleccionando última fecha disponible...")

    last_button = collecting_avaible_date_buttons(page)[-1]
    human_delay()
    last_button.click()

    logger.success("🕒 Última fecha seleccionada")
    return True


def select_by_day(page: Page, spanish_day_name: str) -> bool:

    logger.info(f"🕒 Buscando fecha correspondiente a '{spanish_day_name}'")

    for button in collecting_avaible_date_buttons(page):
        text = str_normalizer(button.inner_text())

        if spanish_day_name in text:
            human_delay()
            button.click()
            logger.success(f"🕒 Fecha seleccionada: {text}")
            return True

    logger.warning(f"⛔ No se encontró el día {spanish_day_name}")
    return False
