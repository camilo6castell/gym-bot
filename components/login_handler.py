from core.config import Config
from playwright.sync_api import Page
from utils.logger import logger
from utils.page_utils import (
    monitor_new_page,
    raise_if_captcha,
    wait_for_redirect,
)
from utils.human_behavior import human_delay, human_type, human_click

config = Config(env_file=".env")


def perform_login(page: Page):
    logger.info("🌐 → Abriendo página de login")
    page.goto(config.get("LOGIN_URL"), wait_until="domcontentloaded")

    raise_if_captcha(page)

    # Tipo documento
    logger.info("🫆  → Seleccionando tipo de documento")
    page.wait_for_selector("#tipodoc", timeout=20000)
    human_click(page, "#tipodoc")
    human_delay()
    page.select_option("#tipodoc", value=config.get("COMPENSAR_DOC_TYPE"))
    human_delay()

    # Número documento
    page.wait_for_selector("#numdoc:not([disabled])", timeout=10000)
    logger.info("🫆  → Ingresando número de documento")
    human_type(page, "#numdoc", config.get("COMPENSAR_DOC_NUM"))
    human_delay()

    # Contraseña
    logger.info("🫆  → Ingresando contraseña")
    human_type(page, "#clavepwd", config.get("COMPENSAR_PASSWORD"))
    human_delay()
    raise_if_captcha(page)

    # Scroll leve antes de enviar (comportamiento natural)
    page.mouse.wheel(0, 200)
    human_delay()

    # Submit
    logger.info("🕒 → Enviando formulario")
    page.wait_for_selector("button[type='submit']:not([disabled])", timeout=5000)
    human_click(page, "button[type='submit']")

    # After login, there's an unexpected "Entiendo" button (cookie/privacy related).
    # If it appears, we click it and continue. This is handled in monitor_new_page.
    monitor_new_page(page, config.get("POTENTIAL_MODAL_ENTIENDO_SELECTOR"))

    wait_for_redirect(page, config.get("POST_LOGIN_URL"))
