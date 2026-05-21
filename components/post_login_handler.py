from core.config import Config
from playwright.sync_api import Page
from utils.logger import logger
from utils.page_utils import (
    monitor_new_page,
    search_and_click,
    wait_for_redirect,
)

config = Config(env_file=".env")


config_environment = config.get("APP_CONFIG").get("environment", {})
config_selectors = config.get("APP_CONFIG").get("selectors", {})


def perform_post_login(page: Page):
    logger.info("🚀 → Iniciando flujo post-login")
    search_and_click(page, "a[href='#mm-m1-p2']")
    search_and_click(
        page, "a[href='/sistema.php/entrenamiento/reserva/practica/libre']"
    )
    monitor_new_page(
        page, config_selectors.get("potential_intermediate_login_selector")
    )
    wait_for_redirect(page, config_environment.get("inside_system_url_pattern"))
    logger.info("✅ → Flujo post-login completado, dentro del sistema.")
