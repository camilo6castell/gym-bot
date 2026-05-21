from core.config import Config
from playwright.sync_api import Page
from utils.logger import logger
from utils.page_utils import (
    monitor_new_page,
    search_and_click,
    wait_for_redirect,
)

config = Config(env_file=".env")


def perform_post_login(page: Page):
    logger.info("🚀 → Iniciando flujo post-login")
    search_and_click(page, "a[href='#mm-m1-p2']")
    search_and_click(
        page, "a[href='/sistema.php/entrenamiento/reserva/practica/libre']"
    )
    monitor_new_page(page, config.get("POTENTIAL_INTERMEDIATE_LOGIN_SELECTOR"))
    wait_for_redirect(page, config.get("INSIDE_SYSTEM_URL_PATTERN"))
    logger.info("✅ → Flujo post-login completado, dentro del sistema.")
