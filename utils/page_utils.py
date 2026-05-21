from playwright.sync_api import Page, TimeoutError
from utils.logger import logger
from utils.human_behavior import human_click
from utils.recovery import with_soft_recovery
from utils.exceptions import CaptchaDetectedError

CAPTCHA_SELECTORS = [
    "iframe[title='recaptcha challenge expires in two minutes']",
    "iframe[title*='hcaptcha challenge']",
]


def search_and_click(page: Page, selector: str, timeout: int = 5000):
    page.wait_for_selector(selector, timeout=timeout)
    human_click(page, selector)


def raise_if_captcha(page: Page):
    for selector in CAPTCHA_SELECTORS:
        try:
            element = page.query_selector(selector)
        except Exception as e:
            # Error consultando el selector — no es un captcha, es un problema técnico
            logger.debug(f"🔍 → Error consultando selector captcha '{selector}': {e}")
            continue  # seguimos con el siguiente selector, no lanzamos excepción

        if element is None:
            # No encontró el elemento — situación normal, no hay captcha
            continue

        if element.is_visible():
            # Encontró el elemento Y es visible — captcha real activo
            logger.warning(f"🔒 → CAPTCHA detectado: '{selector}'")
            raise CaptchaDetectedError("⚠️ → CAPTCHA detectado. Completar y resumir.")
        else:
            # Encontró el elemento pero está oculto — captcha de setup, no activo
            logger.debug(f"🔍 → Selector captcha encontrado pero oculto: '{selector}'")


def dismiss_if_present(
    page: Page, selector: str, is_mandatory: bool = False, timeout: int = 3000
):
    try:
        # ← espera activa al elemento, no a la red
        page.wait_for_selector(selector, state="visible", timeout=timeout)
        page.click(selector)
        logger.info(f"😉 → Elemento '{selector}' encontrado y clickeado.")
    except TimeoutError:
        if is_mandatory:
            raise RuntimeError(f"❌ → Elemento '{selector}' es obligatorio.")
        logger.debug(f"🗑️ → Elemento '{selector}' no apareció, continuando.")


def wait_network_idle(page: Page, timeout: int = 5000):
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except TimeoutError:
        logger.info("🕒 → wait_network_idle: timeout alcanzado, continuando.")


def wait_for_redirect(page: Page, url_pattern: str | None, timeout: int = 15000):
    try:
        if url_pattern:
            page.wait_for_url(url_pattern, timeout=timeout, wait_until="networkidle")
        else:
            logger.warning(
                "⚠️ → wait_for_redirect: No se proporcionó patrón de URL, omitiendo espera."
            )
            pass
    except TimeoutError:
        raise RuntimeError(
            f"❌ → Mala redirección a '{url_pattern}' | actual: '{page.url}'"
        )


def confirm_url(page: Page, url: str):
    """Navega a url solo si no estamos ya ahí."""
    if page.url != url:
        page.goto(url, wait_until="networkidle")


def monitor_new_page(page: Page, selector: str | None = None):
    """Espera red idle, verifica captcha y descarta modal opcional."""
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
    forced_url: str,
    selector: str | None = None,
    redirect_pattern: str | None = None,
):
    """Navega a forced_url, maneja modal opcional y verifica redirección."""
    logger.info(f"🔀 → Forzando URL: {forced_url[:64]} - URL actual: {page.url[:64]}")
    page.goto(forced_url, wait_until="networkidle")
    monitor_new_page(page, selector)
    if redirect_pattern:
        with_soft_recovery(
            lambda: wait_for_redirect(page, redirect_pattern, timeout=5000),
            page,
            action_name=f"Verificando redirección a '{redirect_pattern}'",
        )
