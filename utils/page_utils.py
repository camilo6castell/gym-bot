from typing import Any
from playwright.sync_api import Page, TimeoutError
from utils.logger import logger
from utils.human_behavior import human_click, human_delay
from utils.recovery import with_soft_recovery

CAPTCHA_SELECTORS = [
    "iframe[title='recaptcha challenge expires in two minutes']",
    "iframe[title*='hcaptcha challenge']",
]


def search_and_click(page: Page, selector: str, timeout: int = 5000):
    wait_network_idle(page, timeout=timeout)
    page.wait_for_selector(selector, timeout=timeout)
    human_click(page, selector)


def raise_if_captcha(page: Page):
    for selector in CAPTCHA_SELECTORS:
        try:
            element = page.query_selector(selector)
        except Exception as e:
            logger.debug(f"Error consultando selector '{selector}': {e}")
            continue
        if element and element.is_visible():
            raise RuntimeError("⚠️ CAPTCHA detectado. Completar y resumir.")


def dismiss_if_present(
    page: Page, selector: str, is_mandatory: bool = False, timeout: int = 3000
):
    try:
        search_and_click(page, selector, timeout=timeout)
        logger.info(f"👀Elemento '{selector}' encontrado y clickeado.")
    except TimeoutError:
        if is_mandatory:
            raise RuntimeError(f"❌ Elemento '{selector}' es obligatorio.")
        logger.debug(f"🗑️Elemento '{selector}' no apareció, Intentando continuar.")


def wait_network_idle(page: Page, timeout: int = 5000):
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except TimeoutError:
        logger.debug("🕒wait_network_idle: timeout alcanzado, continuando.")


def wait_for_redirect(page: Page, url_pattern: str, timeout: int = 15000):
    try:
        page.wait_for_url(url_pattern, timeout=timeout, wait_until="networkidle")
    except TimeoutError:
        raise RuntimeError(f"❌ No se completó la redirección a '{url_pattern}'")


def confirm_url(page: Page, url: str):
    """Navega a url solo si no estamos ya ahí."""
    if page.url != url:
        page.goto(url, wait_until="networkidle")


def monitor_new_page(page: Page, selector: str | None = None):
    """Espera red idle, verifica captcha y descarta modal opcional."""
    human_delay()
    wait_network_idle(page)
    raise_if_captcha(page)
    if selector:
        with_soft_recovery(
            lambda: dismiss_if_present(page, selector),
            page,
            action_name=f"Descartando modal '{selector}'",
        )


def force_url(
    page: Page,
    forced_url,
    selector: str | None = None,
    redirect_pattern: str | None = None,
):
    """Navega a forced_url, maneja modal opcional y verifica redirección."""
    logger.info(f"🔀 Forzando URL: {forced_url[:64]}")
    page.goto(forced_url, wait_until="networkidle")
    monitor_new_page(page, selector)
    if redirect_pattern:
        wait_for_redirect(page, redirect_pattern, timeout=8000)
