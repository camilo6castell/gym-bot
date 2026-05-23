from playwright.sync_api import Page
from src.config.config import Config
from src.utils.logger import logger
from src.utils.page_utils import monitor_new_page, raise_if_captcha
from src.utils.human_behavior import human_delay, human_type, human_click

_config = Config()
_env = _config.get("APP_CONFIG").get("environment", {})
_selectors = _config.get("APP_CONFIG").get("selectors", {})


def perform_login(page: Page) -> None:
    logger.info("🌐 → Abriendo página de login")
    page.goto(_env.get("login_url"), wait_until="domcontentloaded")
    raise_if_captcha(page)

    logger.info("🫆 → Seleccionando tipo de documento")
    page.wait_for_selector("#tipodoc", timeout=20000)
    human_click(page, "#tipodoc")
    human_delay()
    page.select_option("#tipodoc", value=_config.get("COMPENSAR_DOC_TYPE"))
    human_delay()

    page.wait_for_selector("#numdoc:not([disabled])", timeout=10000)
    logger.info("🫆 → Ingresando número de documento")
    human_type(page, "#numdoc", _config.get("COMPENSAR_DOC_NUM"))
    human_delay()

    logger.info("🫆 → Ingresando contraseña")
    human_type(page, "#clavepwd", _config.get("COMPENSAR_PASSWORD"))
    human_delay()
    raise_if_captcha(page)

    page.mouse.wheel(0, 200)
    human_delay()

    logger.info("🕒 → Enviando formulario")
    page.wait_for_selector("button[type='submit']:not([disabled])", timeout=5000)
    human_click(page, "button[type='submit']")

    monitor_new_page(page, _selectors.get("potential_modal_entiendo_selector"))
