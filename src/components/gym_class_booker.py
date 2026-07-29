"""Find and book a specific class within the day's schedule."""

from __future__ import annotations

from playwright.sync_api import Page

from src.components.gym_class_acceptance import ClassAcceptance
from src.components.gym_class_checker import ClassChecker
from src.utils.human_behavior import human_delay
from src.utils.logger import logger
from src.utils.page_utils import wait_network_idle
from src.utils.recovery import Recovery
from src.utils.strings import str_normalizer


class ClassBooker:
    """
    Locate the button for a specific class within the selected day's schedule,
    book it, and verify the reservation went through.
    """

    def __init__(
        self,
        acceptance: ClassAcceptance,
        checker: ClassChecker,
        recovery: Recovery,
    ) -> None:
        self._acceptance = acceptance
        self._checker = checker
        self._recovery = recovery

    def book(self, page: Page, gym_class_name: str, gym_class_hour: str) -> None:
        """Find the class by name and time, book it, and verify the reservation."""
        logger.info(f"🔎 → Looking for class '{gym_class_name}' at '{gym_class_hour}'")

        wait_network_idle(page)
        self._recovery.with_soft_recovery(
            lambda: page.wait_for_selector("#contenedor-horarios", timeout=10000),
            page,
            "Waiting for schedule container",
        )

        buttons = page.query_selector_all("button.btn-theme-inverse:not([disabled])")

        for button in buttons:
            text = str_normalizer(button.inner_text())
            if str_normalizer(gym_class_name) in text and gym_class_hour in text:
                human_delay()
                button.click()
                logger.success("✔️ → Class selected successfully")
                self._recovery.with_soft_recovery(
                    lambda: self._acceptance.confirm(page),
                    page,
                    "Confirming reservation in system",
                )
                self._recovery.with_soft_recovery(
                    lambda: self._checker.verify(page, gym_class_name, gym_class_hour),
                    page,
                    f"Verifying '{gym_class_name}' at '{gym_class_hour}'",
                )
                return

        logger.warning("⛔ → Target class not found or not available")
