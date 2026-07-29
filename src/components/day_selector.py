"""Date selection for class reservation."""

from __future__ import annotations

from playwright.sync_api import ElementHandle, Page

from src.utils.human_behavior import human_delay
from src.utils.logger import logger
from src.utils.page_utils import wait_network_idle
from src.utils.recovery import Recovery
from src.utils.strings import str_normalizer


class DateSelector:
    """Select the reservation date — either the latest available or a specific day."""

    def __init__(self, recovery: Recovery) -> None:
        self._recovery = recovery

    def select_latest_date(self, page: Page) -> bool:
        """Select the last available date in the date picker."""
        logger.info("🏃 → Selecting latest available date...")
        last_button = self._get_available_date_buttons(page)[-1]
        human_delay()
        last_button.click()
        logger.success("✔️ → Latest date selected")
        return True

    def select_by_day(self, page: Page, spanish_day_name: str) -> bool:
        """Find and select the date matching the given day name (in Spanish)."""
        logger.info(f"🔎 → Looking for date matching '{spanish_day_name}'")

        for button in self._get_available_date_buttons(page):
            text = str_normalizer(button.inner_text())
            if spanish_day_name in text:
                human_delay()
                button.click()
                logger.success(f"🕒 → Date selected: {text}")
                return True

        logger.warning(f"⛔ → Day '{spanish_day_name}' not found")
        return False

    def _get_available_date_buttons(self, page: Page) -> list[ElementHandle]:
        wait_network_idle(page)
        self._recovery.with_soft_recovery(
            lambda: page.wait_for_selector("button.botonfecha", timeout=10000),
            page,
            "Waiting for available date buttons",
        )
        return page.query_selector_all("button.botonfecha")
