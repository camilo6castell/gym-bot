from playwright.sync_api import Page
from src.config.config import Config
from src.utils.logger import logger
from src.utils.page_utils import (
    monitor_new_page,
    search_and_click,
    wait_for_redirect,
    wait_network_idle,
)

_config = Config()
_env = _config.get("APP_CONFIG").get("environment", {})
_selectors = _config.get("APP_CONFIG").get("selectors", {})


from playwright.sync_api import Page
from src.config.config import Config
from src.utils.logger import logger
from src.utils.page_utils import (
    monitor_new_page,
    search_and_click,
    wait_for_redirect,
    wait_network_idle,
)

_config = Config()
_env = _config.get("APP_CONFIG").get("environment", {})
_selectors = _config.get("APP_CONFIG").get("selectors", {})


def perform_post_login(page: Page) -> None:
    """
    Ejecuta el flujo de navegación después del inicio de sesión.

    Args:
        page (Page): Objeto de la página de Playwright
    """

    # Espera a que la red esté inactiva después del login
    wait_network_idle(page)

    logger.info("🚀 → Iniciando flujo post-login")

    # Navega a la sección de entrenamiento usando el selector de enlace
    search_and_click(page, "a[href='#mm-m1-p2']")

    # Accede a la página de práctica libre
    search_and_click(
        page, "a[href='/sistema.php/entrenamiento/reserva/practica/libre']"
    )

    # Monitorea nuevas páginas que puedan aparecer durante la navegación
    monitor_new_page(page, _selectors.get("potential_intermediate_login_selector"))

    # Espera a que ocurra un redireccionamiento a la URL del sistema
    wait_for_redirect(page, _env.get("inside_system_url_pattern"))

    logger.info("✅ → Flujo post-login completado, dentro del sistema.")
