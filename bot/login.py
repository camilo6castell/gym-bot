import os
import random
import time
from playwright.sync_api import Page
from loguru import logger
from dotenv import load_dotenv
from bot.browser import save_session

# Importar las funciones de comportamiento humano
from .browser import (
    human_delay,
    human_click,
    human_type,
    human_mouse_move,
    random_scroll,
)

load_dotenv()

LOGIN_URL = (
    "https://seguridad.compensar.com/views/index.html"
    "?serviceProviderName=HER-SP&protocol=SAML"
)


def login(page: Page):
    doc_type = os.getenv("COMPENSAR_DOC_TYPE", "")
    doc_num = os.getenv("COMPENSAR_DOC_NUM", "")
    password = os.getenv("COMPENSAR_PASSWORD", "")

    if not all([doc_type, doc_num, password]):
        raise RuntimeError("❌ Faltan variables de entorno del login")

    logger.info("Abriendo página de login")

    # Navegar con wait_until más específico
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    human_delay(1, 2)

    # Hacer scroll aleatorio inicial
    random_scroll(page)

    logger.info("Seleccionando tipo de documento")
    # Primero mover mouse sobre el select
    human_mouse_move(page, "select")
    human_delay(0.5, 1)

    # Click humano en el select
    human_click(page, "select")
    human_delay(0.3, 0.7)

    # Seleccionar opción
    page.select_option("select", value=doc_type)
    human_delay(0.5, 1)

    logger.info("Ingresando número de documento")
    # Escribir como humano
    human_type(page, "#docnum_p", doc_num, min_delay=0.07, max_delay=0.18)

    # Pequeño scroll aleatorio entre campos
    if random.random() > 0.5:
        random_scroll(page)

    logger.info("Ingresando contraseña")
    human_type(page, "#password_p", password, min_delay=0.08, max_delay=0.2)
    human_delay(0.3, 0.6)

    # Quitar foco del input (como humano)
    page.keyboard.press("Tab")
    human_delay(0.5, 1)

    # Ocasionalmente presionar Shift+Tab para volver (como si se corrigiera)
    if random.random() < 0.2:
        page.keyboard.press("Shift+Tab")
        human_delay(0.2, 0.4)
        page.keyboard.press("Tab")
        human_delay(0.2, 0.4)

    logger.info("Click en Ingresar")
    # Esperar a que el botón esté habilitado
    page.wait_for_selector("#btnEnterPersona:not(.disabled)", timeout=30000)

    # Mover mouse sobre el botón
    human_mouse_move(page, "#btnEnterPersona")
    human_delay(0.2, 0.5)

    # Click humano en el botón
    human_click(page, "#btnEnterPersona")
    human_delay(1, 2)

    # Verificar si aparece modal de confirmación
    try:
        logger.info("Verificando modal de confirmación")
        page.wait_for_selector("button:has-text('Entiendo')", timeout=10000)
        human_delay(0.5, 1)
        human_click(page, "button:has-text('Entiendo')")
        logger.info("Modal aceptado")
    except:
        logger.info("No apareció modal de confirmación")

    logger.info("Esperando redirección al sistema interno")

    # Esperar con timeout extendido
    try:
        page.wait_for_url(
            "https://sistemaplanbienestar.deportescompensar.com/**",
            timeout=45000,
            wait_until="networkidle",
        )
    except:
        # Si timeout, verificar si ya estamos en otra página útil
        current_url = page.url
        if "deportescompensar" in current_url:
            logger.info(f"Redirección parcial a: {current_url}")
        else:
            raise Exception("No se completó la redirección esperada")

    human_delay(2, 3)

    # Scroll final para simular exploración
    for _ in range(random.randint(2, 4)):
        random_scroll(page)

    logger.success(f"Login completado. URL actual: {page.url}")
    save_session(page.context)
