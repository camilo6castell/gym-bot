import random
import time
from typing import Optional
from playwright.sync_api import Page, ElementHandle, TimeoutError

from src.utils.logger import logger
from src.utils.human_behavior import human_click
from src.utils.exceptions import CaptchaDetectedError

CAPTCHA_SELECTORS = [
    "iframe[title='recaptcha challenge expires in two minutes']",
    "iframe[title*='hcaptcha challenge']",
]

CAPTCHA_HARD_INDICATORS = [
    "g-recaptcha",
    "hcaptcha",
    "cf-challenge",
    "i'm not a robot",
    "verify you are human",
    "verifica que eres humano",
]

CAPTCHA_SOFT_INDICATORS = [
    "checking your browser",
    "just a moment",
]


# ─── Clicks y esperas ────────────────────────────────────────────────────────


def search_and_click(page: Page, selector: str, timeout: int = 5000) -> None:
    page.wait_for_selector(selector, timeout=timeout)
    human_click(page, selector)


def dismiss_if_present(
    page: Page, selector: str, is_mandatory: bool = False, timeout: int = 10000
) -> None:
    try:
        page.wait_for_selector(selector, state="visible", timeout=timeout)
        page.click(selector)
        logger.info(f"😉 → Elemento '{selector}' encontrado y clickeado.")
    except TimeoutError:
        if is_mandatory:
            raise RuntimeError(f"❌ → Elemento '{selector}' es obligatorio.")
        logger.debug(f"🗑️ → Elemento '{selector}' no apareció, continuando.")


def wait_for_element_with_retry(
    page: Page, selector: str, max_retries: int = 3, timeout: int = 10000
) -> Optional[ElementHandle]:
    """Espera un elemento con reintentos y scroll si no aparece."""
    for attempt in range(max_retries):
        try:
            return page.wait_for_selector(selector, timeout=timeout)
        except Exception:
            if attempt == max_retries - 1:
                raise
            logger.debug(
                f"Intento {attempt + 1} fallido para '{selector}', reintentando..."
            )
            time.sleep(random.uniform(1, 3))
            page.evaluate("window.scrollBy(0, 200)")
            time.sleep(0.5)


# ─── Red y navegación ────────────────────────────────────────────────────────


def wait_network_idle(page: Page, timeout: int = 5000) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except TimeoutError:
        logger.debug("🕒 → wait_network_idle: timeout alcanzado, continuando.")


def wait_for_redirect(
    page: Page, url_pattern: str | None, timeout: int = 15000
) -> None:
    if not url_pattern:
        logger.warning("⚠️ → wait_for_redirect: sin patrón de URL, omitiendo.")
        return
    try:
        page.wait_for_url(url_pattern, timeout=timeout, wait_until="networkidle")
    except TimeoutError:
        raise RuntimeError(
            f"❌ → Mala redirección a '{url_pattern}' | actual: '{page.url}'"
        )


def confirm_url(page: Page, url: str) -> None:
    """Navega a url solo si no estamos ya ahí."""
    if page.url != url:
        page.goto(url, wait_until="networkidle")


# ─── CAPTCHA ─────────────────────────────────────────────────────────────────


def raise_if_captcha(page: Page) -> None:
    """Lanza CaptchaDetectedError si hay un captcha activo y visible."""

    # 1. Verificación por contenido HTML
    try:
        content = page.content().lower()
        for indicator in CAPTCHA_SOFT_INDICATORS:
            if indicator in content:
                logger.info("ℹ️ → Verificación pasiva detectada, esperando...")
                page.wait_for_timeout(4000)
                return
        for indicator in CAPTCHA_HARD_INDICATORS:
            if indicator in content:
                raise CaptchaDetectedError(
                    f"⚠️ → CAPTCHA detectado en contenido: '{indicator}'"
                )
    except CaptchaDetectedError:
        raise
    except Exception as e:
        logger.debug(f"🔍 → Error leyendo contenido de página: {e}")

    # 2. Verificación por selectores del DOM
    for selector in CAPTCHA_SELECTORS:
        try:
            element = page.query_selector(selector)
        except Exception as e:
            logger.debug(f"🔍 → Error consultando selector captcha '{selector}': {e}")
            continue

        if element is None:
            continue

        if element.is_visible():
            logger.warning(f"🔒 → CAPTCHA detectado: '{selector}'")
            raise CaptchaDetectedError("⚠️ → CAPTCHA detectado. Completar y resumir.")
        else:
            logger.debug(f"🔍 → Selector captcha oculto (setup): '{selector}'")


# ─── Flujo de página ─────────────────────────────────────────────────────────


def monitor_new_page(page: Page, selector: str | None = None) -> None:
    """Espera red idle, verifica captcha y descarta modal opcional."""
    from src.utils.recovery import with_soft_recovery  # import local — evita circular

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
) -> None:
    """Navega a forced_url, maneja modal opcional y verifica redirección."""
    from src.utils.recovery import with_soft_recovery  # import local — evita circular

    logger.info(f"🔀 → Forzando URL: {forced_url[:64]}")
    page.goto(forced_url, wait_until="networkidle")
    monitor_new_page(page, selector)
    if redirect_pattern:
        with_soft_recovery(
            lambda: wait_for_redirect(page, redirect_pattern, timeout=5000),
            page,
            action_name=f"Verificando redirección a '{redirect_pattern}'",
        )
