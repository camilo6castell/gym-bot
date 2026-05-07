from playwright.sync_api import Page
from bot.gym_class_confirmation_handler import gym_class_confirmation
from bot.gym_class_verification_handler import perform_gym_class_verification
from utils.logger import logger
from utils.human_behavior import human_delay
from utils.recovery import with_soft_recovery
from utils.element_utils import str_normalizer
from utils.page_utils import wait_network_idle


def gym_class_selector(
    page: Page,
    gym_class_name: str,
    gym_class_hour: str,
):

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
            logger.success("✔️  → Clase seleccionada correctamente")
            with_soft_recovery(
                lambda: gym_class_confirmation(page),
                page,
                "Agendando clase en sistema.",
            )
            logger.success(f"🤔 → ¡Reserva de {gym_class_name} completada! (?)")
            with_soft_recovery(
                lambda: perform_gym_class_verification(
                    page,
                    gym_class_name,
                    gym_class_hour,
                ),
                page,
                f"Verificando '{gym_class_name}' a las '{gym_class_hour}'",
            )
            return

    logger.warning("⛔ → Clase objetivo no encontrada o no disponible")
