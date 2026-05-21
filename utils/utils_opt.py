import random
import time
from typing import Optional

from loguru import logger
from playwright.sync_api import Page, ElementHandle


def wait_for_element_with_retry(
    page: Page, selector: str, max_retries: int = 3, timeout: int = 10000
) -> Optional[ElementHandle]:
    """Espera elemento con reintentos inteligentes

    Retorna ElementHandle si se encuentra, None si wait_for_selector devuelve None.
    Puede lanzar excepciones si falla tras los reintentos.
    """
    for attempt in range(max_retries):
        try:
            element = page.wait_for_selector(selector, timeout=timeout)
            return element
        except Exception:
            if attempt == max_retries - 1:
                raise
            logger.warning(
                f"Intento {attempt + 1} fallado para {selector}, reintentando..."
            )
            time.sleep(random.uniform(1, 3))

            # Intentar scroll para hacer visible el elemento
            page.evaluate("window.scrollBy(0, 200)")
            time.sleep(0.5)


def check_for_captcha(page: Page) -> bool:
    """
    Retorna True SOLO si parece un captcha ACTIVO (requiere acción humana).
    Retorna False para verificaciones pasivas (Cloudflare temporal).
    """

    try:
        page_content = page.content().lower()
        current_url = page.url.lower()

        # 🔴 Indicadores fuertes (captcha real)
        hard_indicators = [
            "g-recaptcha",
            "hcaptcha",
            "cf-challenge",
            "captcha",
            "i'm not a robot",
            "verify you are human",
            "verifica que eres humano",
        ]

        for indicator in hard_indicators:
            if indicator in page_content or indicator in current_url:
                logger.warning(f"⚠️ Captcha ACTIVO detectado: {indicator}")
                return True

        # 🟡 Indicadores suaves (Cloudflare / WAF pasivo)
        soft_indicators = [
            "cloudflare",
            "checking your browser",
            "just a moment",
            "verifying",
        ]

        for indicator in soft_indicators:
            if indicator in page_content:
                logger.info("ℹ️ Verificación pasiva detectada (Cloudflare/WAF)")
                return False

        # 🔴 Selectores explícitos de captcha real
        captcha_selectors = [
            ".g-recaptcha",
            ".h-captcha",
            "iframe[src*='captcha']",
            "iframe[src*='recaptcha']",
        ]

        for selector in captcha_selectors:
            if page.query_selector(selector):
                logger.warning(f"⚠️ Elemento de captcha activo detectado: {selector}")
                return True

    except Exception as e:
        logger.debug(f"Error verificando captcha: {e}")

    return False


def handle_page_load(page: Page, wait_on_soft_captcha: bool = True) -> bool:
    """
    Manejo inteligente de carga:
    - Espera networkidle
    - Scroll humano
    - Tolera verificaciones pasivas
    - Falla solo ante captcha real
    """

    try:
        # Esperar carga base
        page.wait_for_load_state("networkidle", timeout=30000)

        # Pausa humana inicial
        time.sleep(random.uniform(0.5, 1.5))

        # Scroll aleatorio para parecer humano
        for _ in range(random.randint(1, 3)):
            scroll_amount = random.randint(100, 400)
            direction = random.choice([-1, 1])
            page.evaluate(f"window.scrollBy(0, {scroll_amount * direction})")
            time.sleep(random.uniform(0.2, 0.5))

        # Verificar captcha activo
        if check_for_captcha(page):
            logger.error("❌ → Captcha activo detectado. Necesita intervención manual.")
            page.screenshot(path="captcha_detected.png")
            return False

        # Esperar verificaciones pasivas (Cloudflare toast / overlay)
        if wait_on_soft_captcha:
            logger.info("⏳ → Esperando posibles verificaciones pasivas...")
            page.wait_for_timeout(5000)

        return True

    except Exception as e:
        logger.error(f"❌ → Error durante handle_page_load: {e}")
        return False
