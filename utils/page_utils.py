from playwright.sync_api import Page
from utils.logger import logger
from utils.human_behavior import human_click, human_delay

CAPTCHA_SELECTORS = [
    # ← solo el challenge activo, no el setup
    "iframe[title='recaptcha challenge expires in two minutes']",
    "iframe[title*='hcaptcha challenge']",
]


def raise_if_captcha(page: Page):
    for selector in CAPTCHA_SELECTORS:
        try:
            element = page.query_selector(selector)
        except Exception as e:
            logger.debug(f"Error consultando selector '{selector}': {e}")
            continue
        if element and element.is_visible():
            raise RuntimeError("⚠️ CAPTCHA detectado")


def check_unexpected_element(page: Page, selector: str, timeout: int = 3000):
    try:
        page.wait_for_selector(selector, timeout=timeout)
        human_click(page, selector)
        logger.info(f"⚠️ Element '{selector}' acepted and clicked.")
    except TimeoutError:
        logger.info(f"⚠️ Timeout for element '{selector}' to appear.")
        pass


def wait_network_idle(page: Page, timeout: int = 5000):
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except TimeoutError:
        logger.debug("⚠️ wait_network_idle: timeout alcanzado, continuando.")


def wait_for_redirect(page: Page, url_pattern: str, timeout: int = 15000):
    try:
        page.wait_for_url(url_pattern, timeout=timeout, wait_until="networkidle")
    except TimeoutError:
        raise Exception(f"❌ No se completó la redirección a '{url_pattern}'")


def confirm_url(page: Page, url: str):
    if page.url != url:
        page.goto(url, wait_until="networkidle")


def wait_idle_and_search_selector(page: Page, selector: str, timeout: int = 10000):
    wait_network_idle(page, timeout=timeout)
    page.wait_for_selector(selector, timeout=timeout)


# COMPLEX


def monitor_new_page(page: Page, selector: str | None = None):
    human_delay()
    wait_network_idle(page)
    raise_if_captcha(page)
    if selector:
        check_unexpected_element(page, selector)


def force_url(
    page: Page, forced_url: str, selector: str, redirect_page_pattern: str | None = None
):
    logger.info(f"🔀 URL actual: {page.url[:64]}.. | Forzando : {forced_url[:64]}..")
    page.goto(forced_url, wait_until="networkidle")
    monitor_new_page(page, selector)
    if redirect_page_pattern:
        wait_for_redirect(page, redirect_page_pattern, timeout=8000)
    else:
        page.goto(forced_url, wait_until="networkidle")
