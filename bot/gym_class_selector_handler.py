from playwright.sync_api import Page
from bot.gym_class_confirmation_handler import gym_class_confirmation
from utils.logger import logger
from utils.human_behavior import human_delay
from utils.recovery import with_recovery


def gym_class_selector(page: Page, nombre_clase: str, horario: str):

    logger.info(f"🔎 Buscando clase '{nombre_clase}' en horario '{horario}'")

    page.wait_for_selector("#contenedor-horarios", timeout=15000)

    botones = page.query_selector_all("button.btn-theme-inverse:not([disabled])")

    for boton in botones:
        texto = boton.inner_text()

        if nombre_clase.lower() in texto.lower() and horario in texto:
            human_delay()
            boton.click()
            logger.success("✔️ Clase seleccionada correctamente")
            with_recovery(
                lambda: gym_class_confirmation(page),
                page,
                "Confirmando clase seleccionada",
            )
            logger.success(f"🎉 ¡Reserva de {nombre_clase} completada!")
            return

    logger.warning("⛔Clase objetivo no encontrada o no disponible")
