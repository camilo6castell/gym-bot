from playwright.sync_api import Page
from loguru import logger
from bot.browser import human_delay
import os


# ---------------------------------------------------
# UTILIDADES
# ---------------------------------------------------

def normalizar(texto: str):
    return texto.lower().replace("á", "a").replace("é", "e").replace("í", "i") \
        .replace("ó", "o").replace("ú", "u")


# ---------------------------------------------------
# FECHA
# ---------------------------------------------------

def seleccionar_ultima_fecha(page: Page):
    logger.info("Seleccionando última fecha disponible...")

    page.wait_for_selector("button.botonfecha", timeout=15000)
    botones = page.query_selector_all("button.botonfecha")

    ultimo = botones[-1]
    human_delay()
    ultimo.click()

    logger.success("Última fecha seleccionada")


def seleccionar_fecha_por_dia(page: Page, dia_objetivo: str):
    """
    Selecciona fecha cuyo texto contenga el día indicado.
    Ej: 'miércoles 12 junio'
    """

    logger.info(f"Buscando fecha correspondiente a '{dia_objetivo}'")

    dia_objetivo = normalizar(dia_objetivo)

    page.wait_for_selector("button.botonfecha", timeout=15000)
    botones = page.query_selector_all("button.botonfecha")

    for boton in botones:
        texto = normalizar(boton.inner_text())

        if dia_objetivo in texto:
            human_delay()
            boton.click()
            logger.success(f"Fecha seleccionada: {texto}")
            return

    raise RuntimeError(f"No se encontró fecha para el día {dia_objetivo}")


# ---------------------------------------------------
# CLASE
# ---------------------------------------------------

def seleccionar_clase(page: Page, nombre_clase: str, horario: str):
    logger.info(f"Buscando clase '{nombre_clase}' en horario '{horario}'")

    page.wait_for_selector("#contenedor-horarios", timeout=15000)

    botones = page.query_selector_all(
        "button.btn-theme-inverse:not([disabled])"
    )

    for boton in botones:
        texto = boton.inner_text()

        if (
            nombre_clase.lower() in texto.lower()
            and horario in texto
        ):
            human_delay()
            boton.click()
            logger.success("Clase seleccionada correctamente")
            return

    raise RuntimeError("Clase objetivo no encontrada o no disponible")