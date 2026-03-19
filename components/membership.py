from playwright.sync_api import Page
from utils.logger import logger
from utils.page_utils import wait_network_idle


def open_plan_and_use_membership(page: Page):

    logger.info("🔎 Buscando botones 'Usar Membresía' o 'Usar tiquetera'...")

    try:
        # Esperar a que aparezca cualquiera de los dos textos
        page.wait_for_selector(
            'button:has-text("Usar Membresía"), button:has-text("Usar tiquetera")',
            timeout=20000,
        )

        # Locator que contempla ambas opciones
        buttons = page.locator(
            'button:has-text("Usar Membresía"), button:has-text("Usar tiquetera")'
        )

        count = buttons.count()

        if count == 0:
            raise Exception("❌ No se encontraron botones de membresía ni tiquetera.")

        # Buscar el primer botón visible y habilitado
        for i in range(count):
            btn = buttons.nth(i)

            if btn.is_visible() and btn.is_enabled():
                text = btn.inner_text()
                logger.info(f"✔️ Usando botón índice {i} → '{text}'")
                btn.click()
                wait_network_idle(page)
                return

        raise Exception("❌ Se encontraron botones pero ninguno estaba habilitado.")

    except TimeoutError:
        logger.error("⏰ Timeout esperando botones de membresía/tiquetera")
        raise

    except Exception as e:
        logger.error(f"❌ Error seleccionando método de acceso: {e}")
        raise
