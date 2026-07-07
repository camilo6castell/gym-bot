from playwright.sync_api import Page
from src.components.gym_class_acceptance import perform_gym_class_acceptance
from src.components.gym_class_checker import perform_gym_class_checker
from src.utils.logger import logger
from src.utils.human_behavior import human_delay
from src.utils.recovery import recovery
from src.utils.strings import str_normalizer
from src.utils.page_utils import wait_network_idle


def perform_gym_class_booker(
    page: Page, gym_class_name: str, gym_class_hour: str
) -> None:
    logger.info(f"🔎 → Buscando clase '{gym_class_name}' en horario '{gym_class_hour}'")

    wait_network_idle(page)
    recovery.with_soft_recovery(
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
            recovery.with_soft_recovery(
                lambda: perform_gym_class_acceptance(page),
                page,
                "Confirmando reserva en sistema",
            )
            recovery.with_soft_recovery(
                lambda: perform_gym_class_checker(page, gym_class_name, gym_class_hour),
                page,
                f"Verificando '{gym_class_name}' a las '{gym_class_hour}'",
            )
            return

    logger.warning("⛔ → Clase objetivo no encontrada o no disponible")
