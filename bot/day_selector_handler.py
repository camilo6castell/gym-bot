from playwright.sync_api import Page
from utils.logger import logger
from utils.element_utils import str_normalizer
from utils.human_behavior import human_delay


def select_latest_date(page: Page):
    logger.info("Seleccionando última fecha disponible...")

    page.wait_for_selector("button.botonfecha", timeout=15000)
    botones = page.query_selector_all("button.botonfecha")

    ultimo = botones[-1]
    human_delay()
    ultimo.click()

    logger.success("Última fecha seleccionada")


def select_by_day(page: Page, dia_objetivo: str):
    """
    Selecciona fecha cuyo texto contenga el día indicado.
    Ej: 'miércoles 12 junio'
    """

    logger.info(f"Buscando fecha correspondiente a '{dia_objetivo}'")

    dia_objetivo = str_normalizer(dia_objetivo)

    page.wait_for_selector("button.botonfecha", timeout=15000)
    botones = page.query_selector_all("button.botonfecha")

    for boton in botones:
        texto = str_normalizer(boton.inner_text())

        if dia_objetivo in texto:
            human_delay()
            boton.click()
            logger.success(f"Fecha seleccionada: {texto}")
            return

    logger.warning(f"No se encontró fecha para el día {dia_objetivo}")


# ---------------------------------------------------
# CLASE
# ---------------------------------------------------
