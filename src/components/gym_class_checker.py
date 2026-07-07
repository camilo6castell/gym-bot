from playwright.sync_api import Page
from src.utils.human_behavior import human_delay
from src.utils.logger import logger
from src.utils.page_utils import search_and_click, wait_network_idle
from src.utils.time_utils import military_time_range_to_ampm
from src.utils.recovery import recovery
from src.utils.strings import str_normalizer


def perform_gym_class_checker(
    page: Page, gym_class_name: str, gym_class_hour: str
) -> None:
    logger.info(f"🔍 → Verificando reserva: '{gym_class_name}' | '{gym_class_hour}'")

    wait_network_idle(page, timeout=20000)

    search_and_click(page, "a[href='#mm-m1-p2']")
    search_and_click(page, "a[href='/sistema.php/entrenamiento/mis/turnos']")

    recovery.with_soft_recovery(
        lambda: page.wait_for_selector(
            ".panel-proximos-turno .ng-binding, .panel.panel-shadow .ng-binding",
            timeout=15000,
        ),
        page,
        "Esperando contenido renderizado de turnos",
    )

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
        if nombre_normalizado in texto and hora_normalizada in texto:
            logger.success(
                f"✅ → Reserva confirmada: '{gym_class_name}' | '{ampm_hour}'"
            )
            return

    raise RuntimeError(
        f"❌ No se encontró la reserva de '{gym_class_name}' "
        f"en horario '{ampm_hour}'. La clase puede no haberse reservado correctamente."
    )
