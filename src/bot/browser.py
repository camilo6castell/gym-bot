"""
Playwright browser lifecycle management.

Launches a persistent browser context (Chromium or Firefox) with anti-detection
measures (stealth scripts, spoofed geolocation) and exposes the resulting
`Playwright`, `BrowserContext` and `Page` for the automation flow.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from types import TracebackType
from typing import TypedDict, cast

from playwright.sync_api import (
    BrowserContext,
    Geolocation,
    Playwright,
    sync_playwright,
)

from src.types.browser import IPage
from src.types.config import ExecutionConfig, OSConfig
from src.utils.exceptions import BrowserLaunchError
from src.utils.logger import logger


class _CommonContextArgs(TypedDict):
    no_viewport: bool
    permissions: list[str]
    geolocation: Geolocation


class Browser:
    """
    Manages the lifecycle of a Playwright browser with a real user profile.

    This class only launches and closes the browser; it knows nothing about
    login, reservations, or the rest of the business flow.  A `Browser` can
    be used as a context manager to guarantee resource cleanup:

        with Browser(os_config, execution_config, chromium_profile_path) as browser:
            playwright, context, page = browser.launch_chromium()
            ...
    """

    _STEALTH_SCRIPT_BASE = """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    """

    _STEALTH_SCRIPT_CHROMIUM = (
        _STEALTH_SCRIPT_BASE
        + """
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['es-CO', 'es', 'en'] });
        window.chrome = { runtime: {} };
    """
    )

    _STEALTH_SCRIPT_FIREFOX = (
        _STEALTH_SCRIPT_BASE
        + """
        window.chrome = undefined;
    """
    )

    _GEOLOCATION: Geolocation = {"latitude": 4.7110, "longitude": -74.0721}
    _DEFAULT_TIMEOUT_MS = 30000
    _LOCK_FILES = ("SingletonLock", "SingletonCookie", "SingletonSocket")

    def __init__(
        self,
        os_config: OSConfig,
        execution_config: ExecutionConfig,
        chromium_profile_path: str,
        firefox_profile_path: str | None = None,
    ) -> None:
        self._os_config = os_config
        self._execution_config = execution_config
        self._chromium_profile_path = chromium_profile_path
        self._firefox_profile_path = firefox_profile_path

        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None
        self.page: IPage | None = None

    def launch_chromium(self) -> tuple[Playwright, BrowserContext, IPage]:
        """Launch Chromium with the configured real profile and apply stealth."""
        self._kill_existing_chromium()
        logger.info("🌐 → Starting Chromium with real profile")

        playwright = sync_playwright().start()
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=self._chromium_profile_path,
            executable_path=self._os_config.chromium_path,
            headless=self._execution_config.bot_headless,
            args=[
                "--start-maximized",
                "--disable-features=PasswordManagerOnboarding",
                "--disable-save-password-bubble",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-gpu",
                "--disable-gpu-compositing",
                "--disable-gpu-rasterization",
                "--disable-software-rasterizer",
                "--disable-dev-shm-usage",
                "--ozone-platform=x11",
            ],
            ignore_default_args=["--enable-automation", "--no-sandbox"],
            **self._common_context_args(),
        )
        page = self._setup_page(context, self._STEALTH_SCRIPT_CHROMIUM)

        self.playwright, self.context, self.page = playwright, context, page
        return playwright, context, page

    def launch_firefox(self) -> tuple[Playwright, BrowserContext, IPage]:
        """Launch Firefox with the configured real profile and apply stealth."""
        if not self._firefox_profile_path:
            raise BrowserLaunchError("❌ → FIREFOX_PROFILE_NAME not configured in .env")

        logger.info("🦊 → Starting Firefox with real profile")

        playwright = sync_playwright().start()
        context = playwright.firefox.launch_persistent_context(
            user_data_dir=self._firefox_profile_path,
            executable_path=self._os_config.firefox_path,
            headless=self._execution_config.bot_headless,
            locale="es-CO",
            timezone_id="America/Bogota",
            **self._common_context_args(),
        )
        page = self._setup_page(context, self._STEALTH_SCRIPT_FIREFOX)

        self.playwright, self.context, self.page = playwright, context, page
        return playwright, context, page

    def close(self) -> None:
        """Close the browser context and stop Playwright safely."""
        if self.context is not None:
            try:
                self.context.close()
            except Exception as e:
                logger.warning(f"⚠️ → Error closing browser context: {e}")

        if self.playwright is not None:
            try:
                self.playwright.stop()
            except Exception as e:
                logger.warning(f"⚠️ → Error stopping Playwright: {e}")

        self.playwright, self.context, self.page = None, None, None

    def __enter__(self) -> Browser:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def _common_context_args(self) -> _CommonContextArgs:
        return {
            "no_viewport": True,
            "permissions": ["geolocation"],
            "geolocation": self._GEOLOCATION,
        }

    def _kill_existing_chromium(self) -> None:
        """Kill orphaned Chromium processes and clean up profile locks."""
        subprocess.run(["pkill", "-x", "chromium"], check=False)

        profile_path = Path(self._chromium_profile_path)
        for lock_file in self._LOCK_FILES:
            lock = profile_path / lock_file
            if lock.exists():
                lock.unlink()
                logger.info(f"🔓 → Lock removed: {lock_file}")

        time.sleep(1)
        logger.info("🧹 → Chromium cleaned up")

    @staticmethod
    def _setup_page(context: BrowserContext, stealth_script: str) -> IPage:
        context.add_init_script(stealth_script)
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(Browser._DEFAULT_TIMEOUT_MS)
        return cast(IPage, page)
