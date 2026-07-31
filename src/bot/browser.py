"""
Playwright browser lifecycle management.

Launches a persistent browser context (Chromium or Firefox) with anti-detection
measures (stealth scripts, spoofed geolocation) and exposes the resulting
`Playwright`, `BrowserContext` and `Page` for the automation flow.

Supports both desktop (real window size) and mobile device emulation
(fixed viewport, touch events, mobile user agent) for Chromium. Firefox
does not support `is_mobile`, so mobile emulation is Chromium-only.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from types import TracebackType
from typing import Any, TypedDict, cast

from playwright.sync_api import (
    BrowserContext,
    Geolocation,
    Playwright,
    ViewportSize,
    sync_playwright,
)

from src.types.browser import IPage
from src.types.config import ExecutionConfig, OSConfig, RunDevice
from src.utils.exceptions import BrowserLaunchError
from src.utils.logger import logger


class _DesktopContextArgs(TypedDict):
    no_viewport: bool
    permissions: list[str]
    geolocation: Geolocation


class _MobileContextArgs(TypedDict):
    viewport: ViewportSize
    user_agent: str
    device_scale_factor: float
    is_mobile: bool
    has_touch: bool
    permissions: list[str]
    geolocation: Geolocation


class _DeviceDescriptor(TypedDict):
    default_browser_type: str
    device_scale_factor: float
    has_touch: bool
    is_mobile: bool
    user_agent: str
    viewport: ViewportSize


_ContextArgs = _DesktopContextArgs | _MobileContextArgs


class Browser:
    """
    Manages the lifecycle of a Playwright browser with a real user profile.

    This class only launches and closes the browser; it knows nothing about
    login, reservations, or the rest of the business flow.  A `Browser` can
    be used as a context manager to guarantee resource cleanup:

        with Browser(os_config, execution_config, chromium_profile_path) as browser:
            playwright, context, page = browser.launch_chromium()
            ...

    To emulate a mobile device (Chromium only), pass a `RunDevice` member:

        with Browser(os_config, execution_config, chromium_profile_path) as browser:
            playwright, context, page = browser.launch_chromium(RunDevice.IPHONE_15_PRO_MAX)
            ...
    """

    _STEALTH_SCRIPT_BASE = """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    """

    _STEALTH_SCRIPT_CHROMIUM_DESKTOP = (
        _STEALTH_SCRIPT_BASE
        + """
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['es-CO', 'es', 'en'] });
        window.chrome = { runtime: {} };
    """
    )

    _STEALTH_SCRIPT_CHROMIUM_MOBILE = (
        _STEALTH_SCRIPT_BASE
        + """
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

    # Desktop-only args; Chromium refuses to combine these with a fixed viewport.
    _MOBILE_INCOMPATIBLE_ARGS = {"--start-maximized"}

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

    def launch_chromium(
        self, device: RunDevice = RunDevice.DESKTOP
    ) -> tuple[Playwright, BrowserContext, IPage]:
        """
        Launch Chromium with the configured real profile and apply stealth.

        Args:
            device: Device profile to emulate. `RunDevice.DESKTOP` uses the
                real window size; any mobile member emulates a phone.
        """
        self._kill_existing_chromium()
        mode_label = f"mobile ({device.value})" if device is not RunDevice.DESKTOP else "desktop"
        logger.info(f"🌐 → Starting Chromium with real profile [{mode_label}]")

        playwright = sync_playwright().start()
        self.playwright = playwright

        context_args = cast(dict[str, Any], self._common_context_args(device))
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=self._chromium_profile_path,
            executable_path=self._os_config.chromium_path,
            headless=self._execution_config.bot_headless,
            args=self._chromium_launch_args(device),
            ignore_default_args=["--enable-automation", "--no-sandbox"],
            **context_args,
        )
        stealth_script = (
            self._STEALTH_SCRIPT_CHROMIUM_MOBILE
            if device is not RunDevice.DESKTOP
            else self._STEALTH_SCRIPT_CHROMIUM_DESKTOP
        )
        page = self._setup_page(context, stealth_script)

        self.context, self.page = context, page
        return playwright, context, page

    def launch_firefox(self) -> tuple[Playwright, BrowserContext, IPage]:
        """
        Launch Firefox with the configured real profile and apply stealth.

        Note: Firefox does not support `is_mobile` in Playwright, so mobile
        device emulation is only available via `launch_chromium`.
        """
        if not self._firefox_profile_path:
            raise BrowserLaunchError("❌ → FIREFOX_PROFILE_NAME not configured in .env")

        logger.info("🦊 → Starting Firefox with real profile")

        playwright = sync_playwright().start()
        self.playwright = playwright

        context_args = cast(dict[str, Any], self._common_context_args())
        context = playwright.firefox.launch_persistent_context(
            user_data_dir=self._firefox_profile_path,
            executable_path=self._os_config.firefox_path,
            headless=self._execution_config.bot_headless,
            locale="es-CO",
            timezone_id="America/Bogota",
            **context_args,
        )
        page = self._setup_page(context, self._STEALTH_SCRIPT_FIREFOX)

        self.context, self.page = context, page
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

    def _chromium_launch_args(self, device: RunDevice) -> list[str]:
        """Build Chromium CLI args, dropping flags incompatible with mobile emulation."""
        args = [
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
        ]
        if device is not RunDevice.DESKTOP:
            args = [a for a in args if a not in self._MOBILE_INCOMPATIBLE_ARGS]
        return args

    def _common_context_args(self, device: RunDevice = RunDevice.DESKTOP) -> _ContextArgs:
        """
        Build the context kwargs shared by Chromium/Firefox launches.

        When `device` is a mobile member, the browser must already be started
        (`self.playwright` set) so the built-in device descriptor can be
        looked up from `playwright.devices`.
        """
        if device is RunDevice.DESKTOP:
            return {
                "no_viewport": True,
                "permissions": ["geolocation"],
                "geolocation": self._GEOLOCATION,
            }

        if self.playwright is None:
            raise BrowserLaunchError(
                "❌ → Playwright must be started before resolving a mobile device profile"
            )

        playwright: Any = self.playwright
        try:
            descriptor = cast(_DeviceDescriptor, playwright.devices[device.value])
        except KeyError as e:
            raise BrowserLaunchError(
                f"❌ → Unknown mobile device '{device.value}'. "
                "See Playwright's device descriptor list for valid names."
            ) from e

        return {
            "viewport": descriptor["viewport"],
            "user_agent": descriptor["user_agent"],
            "device_scale_factor": descriptor["device_scale_factor"],
            "is_mobile": descriptor["is_mobile"],
            "has_touch": descriptor["has_touch"],
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
