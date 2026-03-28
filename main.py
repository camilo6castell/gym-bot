from bot.browser import launch_browser
from bot.login import perform_login
from bot.logout import perform_logout
from bot.post_login_flow import perform_post_login_flow
from bot.reserve_gym_class import perform_reserve_gym_class

from utils.error_broadcast import send_error_broadcast
from utils.logger import logger
from utils.recovery import with_recovery, with_soft_recovery
from utils.time_utils import spanish_day_mapper
from utils.element_utils import str_normalizer

from components.bot_run import get_classes

from core import env


def main():

    # 1. Validar credenciales — estas SÍ deben existir siempre
    if not all(
        [
            env.COMPENSAR_DOC_TYPE,
            env.COMPENSAR_DOC_NUM,
            env.COMPENSAR_PASSWORD,
            env.LOGIN_URL,
            env.POST_LOGIN_URL,
            env.GYM_CLASS_VERIFICATION_URL,
            env.POTENTIAL_MODAL_ENTIENDO_SELECTOR,
            env.POTENTIAL_INTERMEDIATE_LOGIN_SELECTOR,
            env.INSIDE_SYSTEM_PATTERN_URL,
            env.INSIDE_SYSTEM_URL_PATTERN,
        ]
    ):
        logger.error("❌ Faltan credenciales de acceso en .env")
        return

    # 2. Obtener clases — la lógica force/regular ya está en get_classes
    tentative_classes = get_classes(
        env.BOT_FORCE_RUN,
        env.BOT_FORCE_RUN_CLASS,
        env.BOT_FORCE_RUN_HOUR,
        env.BOT_FORCE_RUN_DAY,
        env.ADDITIONAL_MINUTE_FOR_EXECUTION,
    )

    if not tentative_classes:
        # logger.info("📭 No hay clases para ejecutar en este momento.")
        return

    playwright, context, page = launch_browser(headless=env.BOT_HEADLESS)

    try:

        with_recovery(
            lambda: perform_login(
                page,
                env.COMPENSAR_DOC_TYPE,
                env.COMPENSAR_DOC_NUM,
                env.COMPENSAR_PASSWORD,
                env.LOGIN_URL,
                env.POST_LOGIN_URL,
                env.POTENTIAL_MODAL_ENTIENDO_SELECTOR,
            ),
            page,
            "Proceso de login",
        )

        with_soft_recovery(
            lambda: perform_post_login_flow(
                page,
                env.POTENTIAL_INTERMEDIATE_LOGIN_SELECTOR,
                env.INSIDE_SYSTEM_PATTERN_URL,
            ),
            page,
            "Flujo post-login",
        )

        logger.info(f"🥁 → Iniciando iteraciones de clases. URL: {page.url}")

        for index, gym_class in enumerate(tentative_classes):
            spanish_day_name = spanish_day_mapper(str_normalizer(gym_class["day"]))
            logger.info(
                f"🎯 → Intentando clase {index+1}/{len(tentative_classes)}: "
                f"{gym_class['name']} | {gym_class['hour']} | {spanish_day_name}"
            )

            try:
                with_recovery(
                    lambda: perform_reserve_gym_class(
                        page,
                        env.INSIDE_SYSTEM_URL_PATTERN,
                        spanish_day_name,
                        env.BOT_FORCE_RUN,
                        gym_class["name"],
                        gym_class["hour"],
                        env.GYM_CLASS_VERIFICATION_URL,
                        env.POTENTIAL_INTERMEDIATE_LOGIN_SELECTOR,
                        env.INSIDE_SYSTEM_PATTERN_URL,
                    ),
                    page,
                    f"Reservando '{gym_class['name']}' | {spanish_day_name}",
                )

            except Exception as e:
                send_error_broadcast(
                    page, f"❌ → Error reservando {gym_class['name']}: {e}"
                )

            if index < len(tentative_classes) - 1:
                logger.info("⏳ → Esperando 60 segundos para siguiente clase...")
                page.wait_for_timeout(60000)

        logger.success("🏁 → Flujo completado")

    except Exception as e:
        send_error_broadcast(page, f"❌ → Error general durante la ejecución: {e}")
    finally:
        try:
            perform_logout(page)
        except Exception as logout_error:
            logger.warning(f"❌ → Error en logout: {logout_error}")
        try:
            context.close()
            playwright.stop()
        except:
            pass


if __name__ == "__main__":
    main()
