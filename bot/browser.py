import os
from playwright.sync_api import sync_playwright
from loguru import logger


HOME = os.path.expanduser("~")

# ----------------------------
# FIREFOX (USANDO UN PERFIL REAL)
# ----------------------------
FIREFOX_PATH = "/usr/bin/firefox"


def launch_firefox(headless=False):

    FIREFOX_PROFILE_PATH = os.path.join(
        HOME, ".config", ".mozilla", "firefox", f"edirvssi.gym-bot"
    )

    playwright = sync_playwright().start()

    context = playwright.firefox.launch_persistent_context(
        user_data_dir=FIREFOX_PROFILE_PATH,
        executable_path=FIREFOX_PATH,
        headless=headless,
        args=[],  # Firefox ignora la mayoría de flags de Chromium
        no_viewport=True,
        permissions=["geolocation"],
        geolocation={"latitude": 4.7110, "longitude": -74.0721},
        locale="es-CO",  # reemplaza el navigator.languages del stealth
        timezone_id="America/Bogota",
    )

    # Stealth — Firefox ya no expone navigator.webdriver por defecto
    # pero lo dejamos por si acaso
    context.add_init_script(
        """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = undefined; 
        """
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.set_default_timeout(30000)

    return playwright, context, page


# ----------------------------
# CHROMIUM (USANDO TU PERFIL REAL)
# ----------------------------

# REAL_PROFILE_PATH = os.path.join(HOME, ".config", "chromium-bot")
REAL_PROFILE_PATH = os.path.join(HOME, ".config", "chromium")
CHROMIUM_PATH = "/usr/bin/chromium"


def launch_chromium(headless=False):
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
        ignore_default_args=["--enable-automation", "--no-sandbox"],
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
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['es-CO', 'es', 'en']
            });
            window.chrome = { runtime: {} };
        """
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.set_default_timeout(30000)

    return playwright, context, page
