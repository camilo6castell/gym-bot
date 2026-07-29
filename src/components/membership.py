"""Membership / access method selection before booking."""

from __future__ import annotations

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from src.types.browser import IPage
from src.utils.exceptions import MembershipNotFoundError
from src.utils.logger import logger
from src.utils.page_utils import wait_network_idle
from src.utils.recovery import Recovery


class MembershipSelector:
    """Select the first enabled 'Usar Membresía' / 'Usar tiquetera' button."""

    _SELECTOR = 'button:has-text("Usar Membresía"), button:has-text("Usar tiquetera")'

    def __init__(self, recovery: Recovery) -> None:
        self._recovery = recovery

    def use_membership(self, page: IPage) -> None:
        """
        Find and click the first available access method button.

        Raises
        ------
        MembershipNotFoundError
            If no membership/ticket buttons are found or none are enabled.
        """
        logger.info("🔎 → Looking for 'Usar Membresía' or 'Usar tiquetera' buttons...")

        try:
            self._recovery.with_soft_recovery(
                lambda: page.wait_for_selector(self._SELECTOR, timeout=5000),
                page,
                "Waiting for membership/ticket buttons",
            )

            buttons = page.locator(self._SELECTOR)
            count = buttons.count()

            if count == 0:
                raise MembershipNotFoundError("❌ → No membership or ticket buttons found.")

            for i in range(count):
                btn = buttons.nth(i)
                if btn.is_visible() and btn.is_enabled():
                    logger.info(f"✔️ → Using button '{btn.inner_text()}'")
                    btn.click()
                    wait_network_idle(page)
                    return

            raise MembershipNotFoundError("❌ → Found membership buttons but none were enabled.")

        except PlaywrightTimeoutError:
            logger.error("⏰ → Timeout waiting for membership/ticket buttons")
            raise
        except MembershipNotFoundError:
            raise
        except Exception as e:
            logger.error(f"❌ → Error selecting access method: {e}")
            raise
