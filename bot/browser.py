import os
from playwright.sync_api import sync_playwright
from loguru import logger

HOME = os.path.expanduser("~")
# REAL_PROFILE_PATH = os.path.join(HOME, ".config", "chromium-bot")
REAL_PROFILE_PATH = os.path.join(HOME, ".config", "chromium")
CHROMIUM_PATH = "/usr/bin/chromium"

# ----------------------------
# BROWSER (USANDO TU PERFIL REAL)
# ----------------------------


def launch_browser(headless=False):
    playwright = sync_playwright().start()

    context = playwright.chromium.launch_persistent_context(
        user_data_dir=REAL_PROFILE_PATH,
        executable_path=CHROMIUM_PATH,
        headless=headless,
        args=[
            "--start-maximized",
            "--disable-features=PasswordManagerOnboarding",
            "--disable-save-password-bubble",
            "--disable-blink-features=AutomationControlled",  # ← importante
            "--no-first-run",
            "--no-default-browser-check",
        ],
        ignore_default_args=["--enable-automation"],
        no_viewport=True,
        permissions=["geolocation"],
        geolocation={"latitude": 4.7110, "longitude": -74.0721},
    )

    # stealth básico limpio
    context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]  // plugins reales tienen contenido
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['es-CO', 'es', 'en']  // coherente con tu geolocation
        });
        window.chrome = {
            runtime: {}  // chromium sin esto parece headless
        };
    """
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.set_default_timeout(30000)

    return playwright, context, page
