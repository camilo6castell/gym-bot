"""Generic Playwright page interaction utilities."""

from __future__ import annotations

import random
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from src.types.browser import IElementHandle, IPage
from src.utils.exceptions import CaptchaDetectedError, ElementNotFoundError, RedirectTimeoutError
from src.utils.human_behavior import human_click
from src.utils.logger import logger
from src.utils.recovery import Recovery

CAPTCHA_SELECTORS = [
    "iframe[title='recaptcha challenge expires in two minutes']",
    "iframe[title*='hcaptcha challenge']",
]

CAPTCHA_HARD_INDICATORS = [
    # "g-recaptcha",
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


def search_and_click(page: IPage, selector: str, timeout: int = 5000) -> None:
    page.wait_for_selector(selector, timeout=timeout)
    human_click(page, selector)


def navigate_by_clicks(page: IPage, selectors: list[str], timeout: int = 5000) -> None:
    for selector in selectors:
        search_and_click(page, selector, timeout)


def dismiss_if_present(
    page: IPage, selector: str, is_mandatory: bool = False, timeout: int = 15000
) -> None:
    try:
        page.wait_for_selector(selector, state="visible", timeout=timeout)
        page.click(selector)
        logger.info(f"😉 → Elemento '{selector}' encontrado y clickeado.")
    except PlaywrightTimeoutError as err:
        if is_mandatory:
            raise ElementNotFoundError(f"❌ → Elemento '{selector}' es obligatorio.") from err
        logger.debug(f"🗑️ → Elemento '{selector}' no apareció, continuando.")


def wait_for_element_with_retry(
    page: IPage, selector: str, max_retries: int = 3, timeout: int = 10000
) -> IElementHandle | None:
    """Wait for an element with retries and scroll fallback."""
    for attempt in range(max_retries):
        try:
            return page.wait_for_selector(selector, timeout=timeout)
        except Exception:
            if attempt == max_retries - 1:
                raise
            logger.debug(f"Attempt {attempt + 1} failed for '{selector}', retrying...")
            time.sleep(random.uniform(1, 3))
            page.evaluate("window.scrollBy(0, 200)")
            time.sleep(0.5)
    return None


def wait_for_element_with_progessive_waiting(
    page: IPage, selector: str, max_retries: int = 3, initial_timeout: int = 3000
) -> IElementHandle | None:
    """Wait for an element with progressive waiting and retries."""
    timeout = initial_timeout
    for attempt in range(max_retries):
        wait_network_idle(page, timeout=5000)
        try:
            return page.wait_for_selector(selector, timeout=timeout)
        except Exception:
            if attempt == max_retries - 1:
                raise
            logger.debug(f"Attempt {attempt + 1} failed for '{selector}', retrying...")
            time.sleep(random.uniform(1, 3))
            timeout += initial_timeout
    return None


# ─── Red y navegación ────────────────────────────────────────────────────────


def wait_network_idle(page: IPage, timeout: int = 5000) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except PlaywrightTimeoutError:
        logger.warning(f"🕒 → wait_network_idle timeout for {page.url}, continuing.")


def wait_for_redirect(page: IPage, url_pattern: str | None, timeout: int = 15000) -> None:
    if not url_pattern:
        logger.warning("⚠️ → wait_for_redirect: no URL pattern provided, skipping.")
        return
    try:
        page.wait_for_url(url_pattern, timeout=timeout, wait_until="networkidle")
    except PlaywrightTimeoutError as err:
        raise RedirectTimeoutError(
            f"❌ → Bad redirect to '{url_pattern}' | actual: '{page.url}'"
        ) from err


def confirm_url(page: IPage, url: str) -> None:
    """Navigate to url only if we are not already there."""
    if page.url != url:
        page.goto(url, wait_until="networkidle")


# ─── CAPTCHA ─────────────────────────────────────────────────────────────────


def raise_if_captcha(page: IPage) -> None:
    """Raise CaptchaDetectedError if an active CAPTCHA is found."""

    # 1. Check HTML content for known indicators
    try:
        content = page.content().lower()
        for indicator in CAPTCHA_SOFT_INDICATORS:
            if indicator in content:
                logger.info("ℹ️ → Passive verification detected, waiting...")
                page.wait_for_timeout(4000)
                return
        for indicator in CAPTCHA_HARD_INDICATORS:
            if indicator in content:
                raise CaptchaDetectedError(f"⚠️ → CAPTCHA detected in content: '{indicator}'")
    except CaptchaDetectedError:
        raise
    except Exception as e:
        logger.debug(f"🔍 → Error reading page content: {e}")

    # 2. Check via DOM selectors
    for selector in CAPTCHA_SELECTORS:
        try:
            element = page.query_selector(selector)
        except Exception as e:
            logger.debug(f"🔍 → Error querying captcha selector '{selector}': {e}")
            continue

        if element is None:
            continue

        if element.is_visible():
            logger.warning(f"🔒 → CAPTCHA detected: '{selector}'")
            raise CaptchaDetectedError("⚠️ → CAPTCHA detected. Solve and resume.")
        else:
            logger.debug(f"🔍 → Captcha selector hidden (setup): '{selector}'")


# ─── Flujo de página ─────────────────────────────────────────────────────────


def monitor_new_page(page: IPage, recovery: Recovery, selector: str | None = None) -> None:
    """Wait for network idle, check CAPTCHA, dismiss optional modal."""
    wait_network_idle(page)
    raise_if_captcha(page)
    if selector:
        recovery.with_soft_recovery(
            lambda: dismiss_if_present(page, selector),
            page,
            action_name=f"Dismissing modal '{selector}'",
        )
        wait_network_idle(page, timeout=20000)


def force_url(
    page: IPage,
    recovery: Recovery,
    forced_url: str,
    selector: str | None = None,
    redirect_pattern: str | None = None,
) -> None:
    """Navigate to forced_url, handle optional modal, verify redirect."""
    logger.info(f"🔀 → Forcing URL: {forced_url[:64]}")
    page.goto(forced_url, wait_until="networkidle")
    monitor_new_page(page, recovery, selector)
    if redirect_pattern:
        recovery.with_soft_recovery(
            lambda: wait_for_redirect(page, redirect_pattern, timeout=5000),
            page,
            action_name=f"Verifying redirect to '{redirect_pattern}'",
        )
