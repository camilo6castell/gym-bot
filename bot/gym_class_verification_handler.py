from playwright.sync_api import Page
from utils.human_behavior import human_delay
from utils.logger import logger
from utils.page_utils import confirm_url, force_url, search_and_click
from utils.time_utils import military_time_range_to_ampm
from utils.recovery import with_soft_recovery
from utils.element_utils import str_normalizer


def perform_gym_class_verification(
    page: Page,
    gym_class_name,
    gym_class_hour,
):

    logger.info(f"🔍 → Verificando reserva: '{gym_class_name}' | '{gym_class_hour}'")

    human_delay()
    search_and_click(page, "a[href='#mm-m1-p2']")
    human_delay()
    search_and_click(page, "a[href='/sistema.php/entrenamiento/mis/turnos']")
    human_delay()

    # Esperar que cargue cualquiera de los dos tipos de tarjetas
    with_soft_recovery(
        lambda: page.wait_for_selector(".panel", timeout=10000),
        page,
        "Esperando tarjetas de turnos",
    )

    ampm_hour = military_time_range_to_ampm(gym_class_hour)

    # 🔥 IMPORTANTE: capturar ambos tipos
    tarjetas = page.query_selector_all(".panel-proximos-turno, .panel.panel-shadow")

    for tarjeta in tarjetas:
        texto = str_normalizer(tarjeta.inner_text())
        nombre_normalizado = str_normalizer(gym_class_name)
        hora_normalizada = str_normalizer(ampm_hour)

        if nombre_normalizado in texto and hora_normalizada in texto:
            logger.success(
                f"✅ → 🎉 ✅ Reserva confirmada: '{gym_class_name}' | '{ampm_hour}'"
            )
            return

    raise RuntimeError(
        f"❌ No se encontró la reserva de '{gym_class_name}' "
        f"en horario '{ampm_hour}'. La clase puede no haberse reservado correctamente. Repitiendo proceso..."
    )
