from playwright.sync_api import Page
from bot.gym_class_confirmation_handler import gym_class_confirmation
from utils.logger import logger
from utils.human_behavior import human_delay
from utils.recovery import with_recovery, with_soft_recovery
from utils.element_utils import str_normalizer
from utils.page_utils import wait_network_idle


def gym_class_selector(page: Page, gym_class_name: str, gym_class_hour: str):

    logger.info(f"🔎 → Buscando clase '{gym_class_name}' en horario '{gym_class_hour}'")

    wait_network_idle(page)
    with_soft_recovery(
        lambda: page.wait_for_selector("#contenedor-horarios", timeout=10000),
        page,
        "Esperando contenedor de horarios",
    )

    botones = page.query_selector_all("button.btn-theme-inverse:not([disabled])")

    for boton in botones:
        texto = str_normalizer(boton.inner_text())
        if str_normalizer(gym_class_name) in texto and gym_class_hour in texto:
            human_delay()
            boton.click()
            logger.success("✔️ → Clase seleccionada correctamente")
            with_soft_recovery(
                lambda: gym_class_confirmation(page),
                page,
                "Confirmando clase seleccionada",
            )
            logger.success(f"🎉 → ¡Reserva de {gym_class_name} completada!")
            return

    logger.warning("⛔ → Clase objetivo no encontrada o no disponible")
