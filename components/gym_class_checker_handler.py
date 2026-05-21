from playwright.sync_api import Page
from utils.human_behavior import human_delay
from utils.logger import logger
from utils.page_utils import search_and_click
from utils.time_utils import military_time_range_to_ampm
from utils.recovery import with_soft_recovery
from utils.element_utils import str_normalizer


def perform_gym_class_checker(
    page: Page,
    gym_class_name: str,
    gym_class_hour: str,
):
    logger.info(f"🔍 → Verificando reserva: '{gym_class_name}' | '{gym_class_hour}'")
    search_and_click(page, "a[href='#mm-m1-p2']")
    search_and_click(page, "a[href='/sistema.php/entrenamiento/mis/turnos']")

    # ✅ Cambio 1 — esperar contenido Angular renderizado, no solo el panel vacío
    with_soft_recovery(
        lambda: page.wait_for_selector(
            ".panel-proximos-turno .ng-binding, .panel.panel-shadow .ng-binding",
            timeout=15000,
        ),
        page,
        "Esperando contenido renderizado de turnos",
    )

    # ✅ Cambio 2 — pausa adicional para que Angular termine el ng-repeat
    human_delay(1.5, 2.5)

    ampm_hour = military_time_range_to_ampm(gym_class_hour)
    nombre_normalizado = str_normalizer(gym_class_name)
    hora_normalizada = str_normalizer(ampm_hour)

    tarjetas = page.query_selector_all(
        ".panel-proximos-turno, .panel.panel-shadow[ng-repeat]"
    )

    logger.info(f"🔍 → Tarjetas encontradas: {len(tarjetas)}")

    for tarjeta in tarjetas:
        texto = str_normalizer(tarjeta.inner_text())
        logger.debug(f"Tarjeta: {texto[:80]}")  # ← quitar cuando funcione
        if nombre_normalizado in texto and hora_normalizada in texto:
            logger.success(
                f"✅ → Reserva confirmada: '{gym_class_name}' | '{ampm_hour}'"
            )
            return

    raise RuntimeError(
        f"❌ No se encontró la reserva de '{gym_class_name}' "
        f"en horario '{ampm_hour}'. La clase puede no haberse reservado correctamente."
    )
