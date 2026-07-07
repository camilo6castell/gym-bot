from playwright.sync_api import Page, TimeoutError
from src.utils.logger import logger
from src.utils.page_utils import wait_network_idle
from src.utils.recovery import recovery

_MEMBERSHIP_SELECTOR = (
    'button:has-text("Usar Membresía"), button:has-text("Usar tiquetera")'
)


def perform_open_plan_and_use_membership(page: Page) -> None:
    logger.info("🔎 → Buscando botones 'Usar Membresía' o 'Usar tiquetera'...")

    try:
        recovery.with_soft_recovery(
            lambda: page.wait_for_selector(_MEMBERSHIP_SELECTOR, timeout=5000),
            page,
            "Esperando botones de membresía/tiquetera",
        )

        buttons = page.locator(_MEMBERSHIP_SELECTOR)
        count = buttons.count()

        if count == 0:
            raise RuntimeError(
                "❌ → No se encontraron botones de membresía ni tiquetera."
            )

        for i in range(count):
            btn = buttons.nth(i)
            if btn.is_visible() and btn.is_enabled():
                logger.info(f"✔️ → Usando botón '{btn.inner_text()}'")
                btn.click()
                wait_network_idle(page)
                return

        raise RuntimeError(
            "❌ → Se encontraron botones pero ninguno estaba habilitado."
        )

    except TimeoutError:
        logger.error("⏰ → Timeout esperando botones de membresía/tiquetera")
        raise
    except RuntimeError:
        raise
    except Exception as e:
        logger.error(f"❌ → Error seleccionando método de acceso: {e}")
        raise
