from playwright.sync_api import Page, TimeoutError
from utils.logger import logger
from utils.page_utils import raise_if_captcha, wait_for_redirect
from utils.human_behavior import human_delay, human_type, human_click


def login(
    COMPENSAR_DOC_TYPE, COMPENSAR_DOC_NUM, COMPENSAR_PASSWORD, LOGIN_URL, page: Page
):

    if not all([COMPENSAR_DOC_TYPE, COMPENSAR_DOC_NUM, COMPENSAR_PASSWORD]):
        raise RuntimeError("❌ Faltan variables de entorno del login")

    logger.info("🌐 Abriendo página de login")
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    human_delay(1.5, 2.5)

    raise_if_captcha(page)

    # Tipo documento
    logger.info("🫆 Seleccionando tipo de documento")
    page.wait_for_selector("#tipodoc", timeout=20000)
    human_click(page, "#tipodoc")
    human_delay(0.6, 1.2)
    page.select_option("#tipodoc", value=COMPENSAR_DOC_TYPE)
    human_delay(0.8, 1.5)

    # Número documento
    page.wait_for_selector("#numdoc:not([disabled])", timeout=10000)
    logger.info("🫆 Ingresando número de documento")
    human_type(page, "#numdoc", COMPENSAR_DOC_NUM)
    human_delay(0.6, 1.2)

    # Contraseña
    logger.info("🫆 Ingresando contraseña")
    human_type(page, "#clavepwd", COMPENSAR_PASSWORD)
    human_delay(0.8, 1.5)
    raise_if_captcha(page)

    # Scroll leve antes de enviar (comportamiento natural)
    page.mouse.wheel(0, 200)
    human_delay(0.4, 0.8)

    # Submit
    logger.info("🕒 Enviando formulario")
    page.wait_for_selector("button[type='submit']:not([disabled])", timeout=5000)
    human_click(page, "button[type='submit']")
    raise_if_captcha(page)

    wait_for_redirect(page, "https://seguridad.compensar.com/**", timeout=20000)
