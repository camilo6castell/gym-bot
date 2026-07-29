"""Login flow for the platform."""

from __future__ import annotations

from playwright.sync_api import Page

from src.types.config import EnvironmentConfig, SelectorsConfig
from src.utils.human_behavior import human_click, human_delay, human_type
from src.utils.logger import logger
from src.utils.page_utils import dismiss_if_present, monitor_new_page, raise_if_captcha
from src.utils.recovery import Recovery


class LoginPage:
    """
    Handle the login process: document type selection, credential entry,
    and form submission.
    """

    def __init__(
        self,
        env_config: EnvironmentConfig,
        selectors_config: SelectorsConfig,
        recovery: Recovery,
        doc_type: str,
        doc_num: str,
        password: str,
    ) -> None:
        self._env = env_config
        self._selectors = selectors_config
        self._recovery = recovery
        self._doc_type = doc_type
        self._doc_num = doc_num
        self._password = password

    def perform_login(self, page: Page) -> None:
        """Execute the full login process on the platform."""
        logger.info("🌐 → Opening login page")
        page.goto(self._env.login_url, wait_until="domcontentloaded")
        raise_if_captcha(page)

        if self._selectors.potential_temporary_platform_notification:
            dismiss_if_present(
                page,
                self._selectors.potential_temporary_platform_notification,
                timeout=5000,
            )

        logger.info("🫆 → Selecting document type")
        page.wait_for_selector("#tipodoc", timeout=20000)
        human_click(page, "#tipodoc")
        human_delay()
        page.select_option("#tipodoc", value=self._doc_type)
        human_delay()

        page.wait_for_selector("#numdoc:not([disabled])", timeout=10000)
        logger.info("🫆 → Entering document number")
        human_type(page, "#numdoc", self._doc_num)
        human_delay()

        logger.info("🫆 → Entering password")
        human_type(page, "#clavepwd", self._password)
        human_delay()
        raise_if_captcha(page)

        page.mouse.wheel(0, 200)
        human_delay()

        logger.info("🕒 → Submitting form")
        page.wait_for_selector("button[type='submit']:not([disabled])", timeout=5000)
        human_click(page, "button[type='submit']")

        monitor_new_page(page, self._recovery, self._selectors.potential_modal_entiendo_selector)
