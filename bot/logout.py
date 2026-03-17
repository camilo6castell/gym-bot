from playwright.sync_api import Page
from utils.logger import logger


def logout(page: Page):
    try:
        logger.info("Intentando cerrar sesión")

        # Esperar que el menú de usuario exista
        page.wait_for_selector("i.dropdown-icon", timeout=5000)

        # Abrir menú
        page.click("i.dropdown-icon")

        # Click en Salir
        page.wait_for_selector("a:has-text('Salir')", timeout=5000)
        page.click("a:has-text('Salir')")

        # Confirmar que volvimos al login o a página pública
        page.wait_for_load_state("networkidle")

        logger.success("✅ Sesión cerrada correctamente")

    except Exception as e:
        # MUY importante: nunca romper el flujo por logout
        logger.warning(f"⚠️ No se pudo cerrar sesión limpiamente: {e}")
