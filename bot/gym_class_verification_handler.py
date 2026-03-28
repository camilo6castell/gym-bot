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
    GYM_CLASS_VERIFICATION_URL,
    POTENTIAL_INTERMEDIATE_LOGIN_SELECTOR,
    INSIDE_SYSTEM_PATTERN_URL,
):

    logger.info(f"🔍 → Verificando reserva: '{gym_class_name}' | '{gym_class_hour}'")

    human_delay()
    search_and_click(page, "a[href='#mm-m1-p2']")
    human_delay()
    search_and_click(page, "a[href='/sistema.php/entrenamiento/mis/turnos']")
    human_delay()

    # Esperar que carguen las tarjetas
    with_soft_recovery(
        lambda: page.wait_for_selector(".panel-proximos-turno", timeout=10000),
        page,
        "Esperando tarjetas de próximos turnos",
    )

    ampm_hour = military_time_range_to_ampm(gym_class_hour)
    tarjetas = page.query_selector_all(".panel-proximos-turno")

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
