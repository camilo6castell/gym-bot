import subprocess
import time
from typing import TypedDict

from playwright.sync_api import (
    BrowserContext,
    Geolocation,
    Page,
    Playwright,
    sync_playwright,
)

from src.settings.provider import Settings
from src.utils.logger import logger

_config = Settings()
_os = _config.get("APP_CONFIG").get("os", {})
_execution = _config.get("APP_CONFIG").get("execution", {})

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


class _CommonContextArgs(TypedDict):
    no_viewport: bool
    permissions: list[str]
    geolocation: Geolocation


_COMMON_CONTEXT_ARGS: _CommonContextArgs = {
    "no_viewport": True,
    "permissions": ["geolocation"],
    "geolocation": _GEOLOCATION,
}


def _kill_existing_chromium() -> None:
    subprocess.run(["pkill", "-x", "chromium"], check=False)

    # Eliminar lock files del perfil
    import pathlib

    profile_path = pathlib.Path(_config.get("CHROMIUM_PROFILE_PATH"))
    for lock_file in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
        lock = profile_path / lock_file
        if lock.exists():
            lock.unlink()
            logger.info(f"🔓 → Lock eliminado: {lock_file}")

    time.sleep(1)
    logger.info("🧹 → Chromium limpiado")


def _setup_page(context: BrowserContext, stealth_script: str) -> Page:
    context.add_init_script(stealth_script)
    page = context.pages[0] if context.pages else context.new_page()
    page.set_default_timeout(30000)
    return page


def launch_firefox() -> tuple[Playwright, BrowserContext, Page]:
    profile_path = _config.get("FIREFOX_PROFILE_PATH")
    if not profile_path:
        raise RuntimeError("❌ → FIREFOX_PROFILE_NAME no configurado en .env")

    logger.info("🦊 → Iniciando Firefox con perfil real")
    playwright = sync_playwright().start()
    context = playwright.firefox.launch_persistent_context(
        user_data_dir=profile_path,
        executable_path=_os.get("firefox_path"),
        headless=_execution.get("headless", False),
        locale="es-CO",
        timezone_id="America/Bogota",
        **_COMMON_CONTEXT_ARGS,
    )
    return playwright, context, _setup_page(context, _STEALTH_SCRIPT_FIREFOX)


def launch_chromium() -> tuple[Playwright, BrowserContext, Page]:
    _kill_existing_chromium()
    logger.info("🌐 → Iniciando Chromium con perfil real")
    playwright = sync_playwright().start()
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=_config.get("CHROMIUM_PROFILE_PATH"),
        executable_path=_os.get("chromium_path"),
        headless=_execution.get("headless", False),
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
        **_COMMON_CONTEXT_ARGS,
    )
    return playwright, context, _setup_page(context, _STEALTH_SCRIPT_CHROMIUM)
