"""Selección del método de acceso (membresía o tiquetera) antes de reservar."""

from __future__ import annotations

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from src.utils.exceptions import MembershipNotFoundError
from src.utils.logger import logger
from src.utils.page_utils import wait_network_idle
from src.utils.recovery import Recovery


class MembershipSelector:
    """Elige el primer botón habilitado de 'Usar Membresía' / 'Usar tiquetera'."""

    _SELECTOR = 'button:has-text("Usar Membresía"), button:has-text("Usar tiquetera")'

    def __init__(self, recovery: Recovery) -> None:
        self._recovery = recovery

    def use_membership(self, page: Page) -> None:
        """
        Busca y hace clic en el primer botón de acceso disponible.

        Raises
        ------
        MembershipNotFoundError
            Si no hay botones de membresía/tiquetera, o ninguno está habilitado.
        """
        logger.info("🔎 → Buscando botones 'Usar Membresía' o 'Usar tiquetera'...")

        try:
            self._recovery.with_soft_recovery(
                lambda: page.wait_for_selector(self._SELECTOR, timeout=5000),
                page,
                "Esperando botones de membresía/tiquetera",
            )

            buttons = page.locator(self._SELECTOR)
            count = buttons.count()

            if count == 0:
                raise MembershipNotFoundError(
                    "❌ → No se encontraron botones de membresía ni tiquetera."
                )

            for i in range(count):
                btn = buttons.nth(i)
                if btn.is_visible() and btn.is_enabled():
                    logger.info(f"✔️ → Usando botón '{btn.inner_text()}'")
                    btn.click()
                    wait_network_idle(page)
                    return

            raise MembershipNotFoundError(
                "❌ → Se encontraron botones pero ninguno estaba habilitado."
            )

        except PlaywrightTimeoutError:
            logger.error("⏰ → Timeout esperando botones de membresía/tiquetera")
            raise
        except MembershipNotFoundError:
            raise
        except Exception as e:
            logger.error(f"❌ → Error seleccionando método de acceso: {e}")
            raise
