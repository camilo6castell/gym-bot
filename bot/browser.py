import os
from playwright.sync_api import sync_playwright
import random
import time
from loguru import logger

HOME = os.path.expanduser("~")
# REAL_PROFILE_PATH = os.path.join(HOME, ".config", "chromium-bot")
REAL_PROFILE_PATH = os.path.join(HOME, ".config", "chromium")

CHROMIUM_PATH = "/usr/bin/chromium"

# ----------------------------
# HUMAN BEHAVIOR
# ----------------------------


def human_delay(min_sec=0.4, max_sec=1.2):
    time.sleep(random.uniform(min_sec, max_sec))


def random_scroll(page):
    scroll_amount = random.randint(150, 450)
    direction = random.choice([-1, 1])
    page.evaluate("window.scrollBy(0, arguments[0])", scroll_amount * direction)
    human_delay(0.3, 0.8)


def human_mouse_move(page, selector):
    try:
        element = page.query_selector(selector)
        if not element:
            return

        box = element.bounding_box()
        if not box:
            return

        start_x = random.randint(100, 600)
        start_y = random.randint(100, 500)
        steps = random.randint(15, 25)

        for i in range(steps):
            progress = i / steps
            x = start_x + (box["x"] - start_x) * progress
            y = start_y + (box["y"] - start_y) * progress

            x += random.uniform(-4, 4)
            y += random.uniform(-4, 4)

            page.mouse.move(x, y)
            time.sleep(random.uniform(0.008, 0.02))

    except Exception:
        pass


def human_click(page, selector):
    try:
        human_mouse_move(page, selector)
        human_delay(0.15, 0.4)

        element = page.query_selector(selector)
        if element:
            box = element.bounding_box()
            if box:
                offset_x = box["width"] * random.uniform(0.3, 0.7)
                offset_y = box["height"] * random.uniform(0.3, 0.7)
                page.mouse.click(box["x"] + offset_x, box["y"] + offset_y)
                return

        page.click(selector)

    except Exception:
        page.click(selector)


def human_type(page, selector, text, min_delay=0.06, max_delay=0.18):
    human_click(page, selector)
    human_delay(0.4, 0.8)

    for char in text:
        page.keyboard.type(char)
        time.sleep(random.uniform(min_delay, max_delay))

        # pequeño error humano ocasional
        if random.random() < 0.02:
            page.keyboard.press("Backspace")
            human_delay(0.1, 0.25)
            page.keyboard.type(char)

        if random.random() < 0.03:
            human_delay(0.2, 0.5)


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
    """
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.set_default_timeout(30000)

    return playwright, None, context, page
