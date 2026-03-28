from playwright.sync_api import Page
from utils.logger import logger
from utils.page_utils import (
    monitor_new_page,
    search_and_click,
    wait_for_redirect,
)
from utils.human_behavior import human_delay


def perform_post_login_flow(
    page: Page,
    POTENTIAL_INTERMEDIATE_LOGIN_SELECTOR: str | None,
    INSIDE_SYSTEM_URL_PATTERN: str | None,
):
    logger.info("🚀 → Iniciando flujo post-login")
    human_delay()
    search_and_click(page, "a[href='#mm-m1-p2']")
    human_delay()
    search_and_click(
        page, "a[href='/sistema.php/entrenamiento/reserva/practica/libre']"
    )
    human_delay()
    monitor_new_page(page, POTENTIAL_INTERMEDIATE_LOGIN_SELECTOR)
    human_delay()
    wait_for_redirect(page, INSIDE_SYSTEM_URL_PATTERN)
    logger.info("✅ → Flujo post-login completado, dentro del sistema.")
