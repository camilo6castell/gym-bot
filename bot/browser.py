from playwright.sync_api import sync_playwright
from pathlib import Path
import random
import time
from loguru import logger
import json

STATE_PATH = Path("bot/state/storage_state.json")
CHROMIUM_PATH = "/usr/bin/chromium"  # Chromium del sistema


# ---------- SESSION ----------

def load_storage_state():
    if not STATE_PATH.exists():
        return None

    try:
        content = STATE_PATH.read_text().strip()
        if not content:
            logger.warning("⚠️ storage_state.json vacío, se ignora")
            return None

        json.loads(content)
        return str(STATE_PATH)

    except Exception as e:
        logger.warning(f"⚠️ storage_state inválido: {e}")
        return None


def save_session(context):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(STATE_PATH))
    logger.info("💾 Sesión guardada correctamente")


# ---------- HUMAN BEHAVIOR ----------

def human_delay(min_sec=0.5, max_sec=2.0):
    time.sleep(random.uniform(min_sec, max_sec))


def random_scroll(page):
    scroll_amount = random.randint(100, 400)
    direction = random.choice([-1, 1])
    page.evaluate(f"window.scrollBy(0, {scroll_amount * direction})")
    human_delay(0.3, 0.8)


def human_mouse_move(page, selector):
    try:
        element = page.query_selector(selector)
        if not element:
            return

        box = element.bounding_box()
        if not box:
            return

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


# ---------- BROWSER ----------

def launch_browser(headless=False):
    playwright = sync_playwright().start()

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    user_agent = random.choice(user_agents)

    args = [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--start-maximized",
        "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding",
        "--disable-backgrounding-occluded-windows",
    ]

    browser = playwright.chromium.launch(
        executable_path=CHROMIUM_PATH,
        headless=headless,
        args=args,
        slow_mo=random.randint(40, 120),
    )

    storage_state = load_storage_state()
    if storage_state:
        logger.info("🔁 Cargando sesión previa")

    context = browser.new_context(
        viewport=None,
        user_agent=user_agent,
        locale="es-CO",
        timezone_id="America/Bogota",
        storage_state=storage_state,
    )

    context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['es-CO','es','en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
        window.chrome = { runtime: {} };
        """
    )

    page = context.new_page()
    page.set_default_timeout(30_000)
    page.set_default_navigation_timeout(30_000)

    logger.info(f"Navegador iniciado con UA: {user_agent[:60]}...")

    return playwright, browser, context, page
