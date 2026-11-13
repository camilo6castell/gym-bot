"""Membership / access method selection before booking."""

from __future__ import annotations

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from src.types.browser import IPage
from src.utils.exceptions import MembershipNotFoundError
from src.utils.logger import logger
from src.utils.page_utils import wait_for_element_with_progessive_waiting, wait_network_idle
from src.utils.recovery import Recovery


class MembershipSelector:
    """Select the membership/ticket button for the configured place."""

    def __init__(self, recovery: Recovery) -> None:
        self._recovery = recovery

    def use_membership(self, page: IPage, place: str) -> None:
        """
        Find and click the access method button for the given place.

        It locates the card whose title matches the configured place and clicks
        its "Usar Membresía" / "Usar tiquetera" button.

        Raises
        ------
        MembershipNotFoundError
            If no matching card/button is found or none are enabled.
        """
        try:
            self._use_membership_for_place(page, place)
        except PlaywrightTimeoutError:
            logger.error("⏰ → Timeout waiting for membership/ticket buttons")
            raise
        except MembershipNotFoundError:
            raise
        except Exception as e:
            logger.error(f"❌ → Error selecting access method: {e}")
            raise

    def _use_membership_for_place(self, page: IPage, place: str) -> None:
        place = place.strip()

        if not place:
            raise MembershipNotFoundError("❌ → 'place' is empty.")

        logger.info(f"🔎 → Looking for membership/ticket button for place '{place}'...")

        safe_place = place.replace("\\", "\\\\").replace('"', '\\"')
        card_selector = f'.widget-tile:has(h5 strong:text-is("{safe_place}"))'

        try:
            wait_for_element_with_progessive_waiting(page, card_selector)
        except PlaywrightTimeoutError as err:
            raise MembershipNotFoundError(
                f"❌ → No membership card found for place '{place}'."
            ) from err

        if page.locator(card_selector).count() == 0:
            raise MembershipNotFoundError(f"❌ → No membership card found for place '{place}'.")

        buttons = page.locator(
            f'{card_selector} button:has-text("Usar Membresía"), '
            f'{card_selector} button:has-text("Usar tiquetera")'
        )
        count = buttons.count()

        if count == 0:
            raise MembershipNotFoundError(
                f"❌ → No membership or ticket buttons found for place '{place}'."
            )

        for i in range(count):
            btn = buttons.nth(i)
            if btn.is_visible() and btn.is_enabled():
                logger.info(f"✔️ → Using button '{btn.inner_text().strip()}' for place '{place}'")
                btn.click()
                wait_network_idle(page)
                return

        raise MembershipNotFoundError(
            f"❌ → Found membership buttons for place '{place}' but none were enabled."
        )
