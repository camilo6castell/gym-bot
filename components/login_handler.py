from core.config import Config
from playwright.sync_api import Page
from utils.logger import logger
from utils.page_utils import (
    monitor_new_page,
    raise_if_captcha,
)
from utils.human_behavior import human_delay, human_type, human_click

config = Config(env_file=".env")

config_environment = config.get("APP_CONFIG").get("environment", {})
config_selectors = config.get("APP_CONFIG").get("selectors", {})


def perform_login(page: Page):
    logger.info("🌐 → Abriendo página de login")
    page.goto(config_environment.get("login_url"), wait_until="domcontentloaded")

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
    monitor_new_page(page, config_selectors.get("potential_modal_entiendo_selector"))

    # wait_for_redirect(page, config.get("APP_CONFIG")["environment"]["post_login_url"])
