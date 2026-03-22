from bot.browser import launch_browser
from bot.login import login
from bot.logout import logout
from bot.reserve_gym_class import reserve_gym_class_handler

from components.bot_run import get_classes

from core import env

from utils.error_broadcast import send_error_broadcast
from utils.logger import logger
from utils.recovery import with_recovery
from utils.days_handler import spanish_day_mapper
from utils.element_utils import str_normalizer
from utils.page_utils import force_url, monitor_new_page


def main():

    # 1. Validar credenciales — estas SÍ deben existir siempre
    if not all(
        [
            env.COMPENSAR_DOC_TYPE,
            env.COMPENSAR_DOC_NUM,
            env.COMPENSAR_PASSWORD,
            env.LOGIN_URL,
            env.POST_LOGIN_URL,
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
            lambda: login(
                env.COMPENSAR_DOC_TYPE,
                env.COMPENSAR_DOC_NUM,
                env.COMPENSAR_PASSWORD,
                env.LOGIN_URL,
                page,
            ),
            page,
            "Proceso de login",
        )

        # Sometimes, after login, there's an unexpected "Entiendo" button (cookie/privacy related).
        # If it appears, we click it and continue. This is handled in monitor_new_page.

        with_recovery(
            lambda: monitor_new_page(page, "button:has-text('Entiendo')"),
            page,
            "Monitoreo de nueva página post-login",
        )

        #

        with_recovery(
            lambda: force_url(
                page,
                env.POST_LOGIN_URL,
                "#presso-login",
                "**deportescompensar.com/**",
            ),
            page,
            "Forzando URL para entrar al plan bienestar",
        )

        logger.success(f"✅ → Login completado: {page.url}")

        for index, gym_class in enumerate(tentative_classes):
            spanish_day_name = spanish_day_mapper(str_normalizer(gym_class["day"]))
            logger.info(
                f"🎯 → Intentando clase {index+1}/{len(tentative_classes)}: "
                f"{gym_class['name']} | {gym_class['hour']} | {spanish_day_name}"
            )

            try:
                with_recovery(
                    lambda: reserve_gym_class_handler(
                        page,
                        env.POST_LOGIN_URL,
                        spanish_day_name,
                        env.BOT_FORCE_RUN,
                        gym_class["name"],
                        gym_class["hour"],
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
            logout(page)
        except Exception as logout_error:
            logger.warning(f"❌ → Error en logout: {logout_error}")
        try:
            context.close()
            playwright.stop()
        except:
            pass


if __name__ == "__main__":
    main()
