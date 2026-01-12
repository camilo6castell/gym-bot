from playwright.sync_api import sync_playwright
from pathlib import Path
import random
import time
from loguru import logger
import json


STATE_PATH = Path("bot/state/storage_state.json")


def load_storage_state():
    """Carga storage_state solo si es válido"""
    if not STATE_PATH.exists():
        return None

    try:
        content = STATE_PATH.read_text().strip()
        if not content:
            logger.warning("⚠️ storage_state.json está vacío, se ignora")
            return None

        json.loads(content)  # validar JSON
        return str(STATE_PATH)

    except Exception as e:
        logger.warning(f"⚠️ storage_state inválido, se ignora: {e}")
        return None


def human_delay(min_sec=0.5, max_sec=2.0):
    """Delay aleatorio entre acciones"""
    time.sleep(random.uniform(min_sec, max_sec))


def random_scroll(page):
    """Hacer scroll aleatorio para parecer humano"""
    scroll_amount = random.randint(100, 400)
    scroll_direction = random.choice([-1, 1])

    page.evaluate(f"window.scrollBy(0, {scroll_amount * scroll_direction})")
    human_delay(0.3, 0.8)


def human_mouse_move(page, selector):
    """Movimiento de mouse más humano hacia un elemento"""
    try:
        element = page.query_selector(selector)
        if element:
            box = element.bounding_box()
            if box:
                start_x = random.randint(100, 300)
                start_y = random.randint(100, 300)

                control_x = random.randint(200, 400)
                control_y = random.randint(200, 400)

                steps = random.randint(8, 15)
                for i in range(steps):
                    t = i / steps
                    x = (
                        (1 - t) ** 2 * start_x
                        + 2 * (1 - t) * t * control_x
                        + t**2 * box["x"]
                    )
                    y = (
                        (1 - t) ** 2 * start_y
                        + 2 * (1 - t) * t * control_y
                        + t**2 * box["y"]
                    )

                    x += random.uniform(-3, 3)
                    y += random.uniform(-3, 3)

                    page.mouse.move(x, y)
                    time.sleep(random.uniform(0.01, 0.03))
    except Exception:
        pass


def human_click(page, selector, force_direct=False):
    """Click que simula comportamiento humano"""
    if not force_direct and random.random() > 0.3:
        human_mouse_move(page, selector)
        human_delay(0.1, 0.3)

    element = page.query_selector(selector)
    if element:
        box = element.bounding_box()
        if box:
            offset_x = box["width"] * random.uniform(0.3, 0.7)
            offset_y = box["height"] * random.uniform(0.3, 0.7)

            page.mouse.click(box["x"] + offset_x, box["y"] + offset_y)
            return

    page.click(selector)


def human_type(page, selector, text, min_delay=0.05, max_delay=0.15):
    """Escribir texto como humano"""
    human_click(page, selector)
    human_delay(0.2, 0.5)

    for char in text:
        page.keyboard.type(char)
        time.sleep(random.uniform(min_delay, max_delay))

        if random.random() < 0.02:
            page.keyboard.press("Backspace")
            human_delay(0.1, 0.2)
            page.keyboard.type(char)

        if random.random() < 0.03:
            human_delay(0.2, 0.4)


def save_session(context):
    """Guarda cookies + localStorage"""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(STATE_PATH))
    logger.info("💾 Sesión guardada correctamente")


def launch_browser(headless=False):
    """Lanza el navegador con configuraciones anti-detección"""

    playwright = sync_playwright().start()

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    ]

    selected_user_agent = random.choice(user_agents)

    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-web-security",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-site-isolation-trials",
        "--disable-features=BlockInsecurePrivateNetworkRequests",
        "--disable-features=SameSiteByDefaultCookies",
        "--disable-features=OutOfBlinkCors",
        "--disable-features=CrossSiteDocumentBlockingAlways",
        "--disable-features=CrossSiteDocumentBlockingIfIsolating",
        "--window-size=1366,768",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-background-networking",
        "--disable-component-extensions-with-background-pages",
        "--disable-default-apps",
        "--disable-extensions",
        "--disable-sync",
        "--metrics-recording-only",
        "--no-first-run",
        "--no-default-browser-check",
        "--start-maximized",
    ]

    browser = playwright.chromium.launch(
        headless=headless,
        args=args,
        slow_mo=random.randint(50, 150),
    )

    # 👉 storage_state separado (corrección clave)
    storage_state = load_storage_state()
    if storage_state:
        logger.info("🔁 Cargando sesión previa")

    context = browser.new_context(
        viewport={"width": 1366, "height": 768},
        user_agent=selected_user_agent,
        locale="es-ES",
        timezone_id="America/Bogota",
        permissions=["geolocation"],
        color_scheme="light",
        java_script_enabled=True,
        has_touch=False,
        is_mobile=False,
        storage_state=storage_state,
    )

    context.set_extra_http_headers(
        {
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": selected_user_agent,
        }
    )

    context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['es-ES','es','en-US','en'] });
        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        window.chrome = { runtime: {} };

        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : originalQuery(parameters)
        );

        Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
        """
    )

    page = context.new_page()
    page.set_default_timeout(30_000)
    page.set_default_navigation_timeout(30_000)

    context.grant_permissions(["geolocation"])

    logger.info(f"Navegador iniciado con User-Agent: {selected_user_agent[:50]}...")

    return playwright, browser, context, page
