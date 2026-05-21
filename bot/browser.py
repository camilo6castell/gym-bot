from core.config import Config
from playwright.sync_api import sync_playwright

config = Config(env_file=".env")
config_os = config.get("APP_CONFIG").get("os", {})
config_execution = config.get("APP_CONFIG").get("execution", {})


# FIREFOX (USANDO UN PERFIL REAL)


def launch_firefox():

    playwright = sync_playwright().start()

    context = playwright.firefox.launch_persistent_context(
        user_data_dir=config.get("FIREFOX_PROFILE_PATH"),
        executable_path=config_os.get("firefox_path"),
        headless=config_execution.get("headless", False),
        args=[],  # Firefox ignora la mayoría de flags de Chromium
        no_viewport=True,
        permissions=["geolocation"],
        geolocation={"latitude": 4.7110, "longitude": -74.0721},
        locale="es-CO",  # reemplaza el navigator.languages del stealth
        timezone_id="America/Bogota",
    )

    # Stealth — Firefox ya no expone navigator.webdriver por defecto
    # pero lo dejamos por si acaso
    context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = undefined; 
        """)

    page = context.pages[0] if context.pages else context.new_page()
    page.set_default_timeout(30000)

    return playwright, context, page


# CHROMIUM (USANDO TU PERFIL REAL)


def launch_chromium():
    playwright = sync_playwright().start()

    context = playwright.chromium.launch_persistent_context(
        user_data_dir=config.get("CHROMIUM_PROFILE_PATH"),
        executable_path=config_os.get("chromium_path"),
        headless=config_execution.get("headless", False),
        args=[
            "--start-maximized",
            "--disable-features=PasswordManagerOnboarding",
            "--disable-save-password-bubble",
            # "--disable-blink-features=AutomationControlled",
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
        no_viewport=True,
        permissions=["geolocation"],
        geolocation={"latitude": 4.7110, "longitude": -74.0721},
    )

    # stealth básico limpio
    context.add_init_script("""
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
        """)

    page = context.pages[0] if context.pages else context.new_page()
    page.set_default_timeout(30000)

    return playwright, context, page
