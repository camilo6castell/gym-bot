from playwright.sync_api import Page
from utils.logger import logger
from utils.page_utils import dismiss_if_present, search_and_click, wait_network_idle
from utils.recovery import with_soft_recovery


def logout(page: Page):
    try:
        logger.info("🚪 → Intentando cerrar sesión")

        dismiss_if_present(page, "notific8-close-button", timeout=3000)

        # Esperar que el menú de usuario exista
        with_soft_recovery(
            lambda: search_and_click(page, "i.dropdown-icon", timeout=5000),
            page,
            "Esperando menú de usuario para logout",
        )

        # Click en Salir
        with_soft_recovery(
            lambda: search_and_click(page, "a:has-text('Salir')", timeout=5000),
            page,
            "Intentando hacer click en 'Salir'",
        )

        # Confirmar que volvimos al login o a página pública
        wait_network_idle(page, timeout=10000)  # Esperar que se complete la navegación

        logger.success("✅ → Sesión cerrada correctamente")

    except Exception as e:
        # MUY importante: nunca romper el flujo por logout
        logger.warning(f"⚠️ → No se pudo cerrar sesión limpiamente: {e}")
