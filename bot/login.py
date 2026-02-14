import os
from playwright.sync_api import Page, TimeoutError
from loguru import logger
from dotenv import load_dotenv

from bot.browser import human_delay, human_type, human_click

load_dotenv()

LOGIN_URL = (
    "https://seguridad.compensar.com/sign-in"
    "?serviceProviderName=HER-SP&protocol=SAML"
)


# ---------------------------------------------------
# UTILIDADES
# ---------------------------------------------------

def wait_network_idle(page: Page, timeout=15000):
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except:
        pass


def wait_if_captcha(page: Page):
    try:
        page.wait_for_selector("iframe[title*='recaptcha']", timeout=3000)
        logger.warning("⚠️ CAPTCHA detectado en pantalla.")
    except TimeoutError:
        pass


# ---------------------------------------------------
# LOGIN PRINCIPAL
# ---------------------------------------------------

def login(page: Page):

    doc_type = os.getenv("COMPENSAR_DOC_TYPE")
    doc_num = os.getenv("COMPENSAR_DOC_NUM")
    password = os.getenv("COMPENSAR_PASSWORD")

    if not all([doc_type, doc_num, password]):
        raise RuntimeError("❌ Faltan variables de entorno del login")

    logger.info("🌐 Abriendo página de login")
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    human_delay(1.5, 2.5)

    wait_if_captcha(page)

    # Tipo documento
    logger.info("Seleccionando tipo de documento")
    page.wait_for_selector("#tipodoc", timeout=20000)
    human_click(page, "#tipodoc")
    human_delay(0.6, 1.2)
    page.select_option("#tipodoc", value=doc_type)
    human_delay(0.8, 1.5)

    page.wait_for_selector("#numdoc:not([disabled])", timeout=10000)

    # Número documento
    logger.info("Ingresando número de documento")
    human_type(page, "#numdoc", doc_num)

    human_delay(0.6, 1.2)

    # Contraseña
    logger.info("Ingresando contraseña")
    human_type(page, "#clavepwd", password)

    human_delay(0.8, 1.5)

    # Scroll leve antes de enviar (comportamiento natural)
    page.mouse.wheel(0, random_scroll := 200)
    human_delay(0.4, 0.8)

    # Submit
    logger.info("Enviando formulario")
    page.wait_for_selector("button[type='submit']:not([disabled])", timeout=15000)
    human_click(page, "button[type='submit']")

    wait_network_idle(page)
    wait_if_captcha(page)

    # Modal opcional
    try:
        page.wait_for_selector("button:has-text('Entiendo')", timeout=6000)
        human_click(page, "button:has-text('Entiendo')")
        logger.info("Modal aceptado")
    except TimeoutError:
        pass

    # Redirección
    logger.info("Esperando redirección final...")

    try:
        page.wait_for_url(
            "**deportescompensar.com/**",
            timeout=45000,
            wait_until="networkidle",
        )
    except TimeoutError:
        raise Exception("❌ No se completó la redirección esperada")

    logger.success(f"✅ Login completado: {page.url}")