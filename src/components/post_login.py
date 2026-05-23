from pathlib import Path
from playwright.sync_api import Page
from src.config.config import Config
from src.utils.logger import logger
from src.utils.page_utils import monitor_new_page, search_and_click, wait_for_redirect

_config = Config(env_file=str(Path(__file__).resolve().parent.parent / ".env"))
_env = _config.get("APP_CONFIG").get("environment", {})
_selectors = _config.get("APP_CONFIG").get("selectors", {})


def perform_post_login(page: Page) -> None:
    logger.info("🚀 → Iniciando flujo post-login")
    search_and_click(page, "a[href='#mm-m1-p2']")
    search_and_click(
        page, "a[href='/sistema.php/entrenamiento/reserva/practica/libre']"
    )
    monitor_new_page(page, _selectors.get("potential_intermediate_login_selector"))
    wait_for_redirect(page, _env.get("inside_system_url_pattern"))
    logger.info("✅ → Flujo post-login completado, dentro del sistema.")
