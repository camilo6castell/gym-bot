from playwright.sync_api import ElementHandle, Page
from src.utils.logger import logger
from src.utils.strings import str_normalizer
from src.utils.human_behavior import human_delay
from src.utils.page_utils import wait_network_idle
from src.utils.recovery import recovery


def perform_select_latest_date(page: Page) -> bool:
    logger.info("🏃 → Seleccionando última fecha disponible...")
    last_button = _get_available_date_buttons(page)[-1]
    human_delay()
    last_button.click()
    logger.success("✔️ → Última fecha seleccionada")
    return True


def perform_select_by_day(page: Page, spanish_day_name: str) -> bool:
    logger.info(f"🔎 → Buscando fecha correspondiente a '{spanish_day_name}'")

    for button in _get_available_date_buttons(page):
        text = str_normalizer(button.inner_text())
        if spanish_day_name in text:
            human_delay()
            button.click()
            logger.success(f"🕒 → Fecha seleccionada: {text}")
            return True

    logger.warning(f"⛔ → No se encontró el día '{spanish_day_name}'")
    return False


def _get_available_date_buttons(page: Page) -> list[ElementHandle]:
    wait_network_idle(page)
    recovery.with_soft_recovery(
        lambda: page.wait_for_selector("button.botonfecha", timeout=10000),
        page,
        "Esperando botones de fecha disponibles",
    )
    return page.query_selector_all("button.botonfecha")
