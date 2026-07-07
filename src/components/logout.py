from playwright.sync_api import Page
from src.utils.logger import logger
from src.utils.human_behavior import human_delay
from src.utils.page_utils import search_and_click, wait_network_idle
from src.utils.recovery import recovery


def perform_logout(page: Page) -> None:
    try:
        logger.info("🚪 → Intentando cerrar sesión")
        human_delay()

        recovery.with_soft_recovery(
            lambda: search_and_click(page, "i.dropdown-icon", timeout=5000),
            page,
            "Esperando menú de usuario para logout",
        )
        human_delay()

        recovery.with_soft_recovery(
            lambda: search_and_click(page, "a:has-text('Salir')", timeout=5000),
            page,
            "Intentando hacer click en 'Salir'",
        )

        wait_network_idle(page, timeout=10000)
        logger.success("✅ → Sesión cerrada correctamente")

    except Exception as e:
        logger.warning(f"⚠️ → No se pudo cerrar sesión limpiamente: {e}")
