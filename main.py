from bot.day_selector_handler import select_by_day, select_latest_date
from bot.gym_class_confirmation_handler import gym_class_confirmation
from bot.browser import launch_browser
from bot.login import login
from bot.logout import logout
from bot.gym_class_selector_handler import gym_class_selector

from components.bot_run import get_classes
from components.membership import open_plan_and_use_membership

from core import env

from utils.error_broadcast import send_error_broadcast
from utils.logger import logger
from utils.recovery import with_recovery
from utils.page_utils import (
    confirm_url,
    force_url,
    monitor_new_page,
)


def main():

    # 1. Validar credenciales — estas SÍ deben existir siempre
    if not all(
        [
            env.COMPENSAR_DOC_TYPE,
            env.COMPENSAR_DOC_NUM,
            env.COMPENSAR_PASSWORD,
            env.LOGIN_URL,
        ]
    ):
        logger.error("❌ Faltan credenciales de acceso en .env")
        return

    # 2. Obtener clases — la lógica force/regular ya está en get_classes
    classes = get_classes(
        env.BOT_FORCE_RUN,
        env.BOT_FORCE_RUN_CLASS,
        env.BOT_FORCE_RUN_HOUR,
        env.BOT_FORCE_RUN_DAY,
        env.ADDITIONAL_MINUTE_FOR_EXECUTION,
    )

    if not classes:
        logger.info("📭 No hay clases para ejecutar en este momento.")
        return

    playwright, browser, context, page = launch_browser(headless=env.BOT_HEADLESS)

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

        with_recovery(
            lambda: monitor_new_page(page, "button:has-text('Entiendo')"),
            page,
            "Monitoreo de nueva página post-login",
        )

        with_recovery(
            lambda: force_url(
                page,
                "https://sistemaplanbienestar.deportescompensar.com/entrenamiento/reserva/practica/libre",
                "#presso-login",
                "**deportescompensar.com/**",
            ),
            page,
            "Forzando URL para entrar al plan bienestar",
        )

        logger.success(f"✅ Login completado: {page.url}")

        for index, gym_class in enumerate(classes):
            logger.info(
                f"🎯 Intentando clase {index+1}/{len(classes)}: "
                f"{gym_class['name']} | {gym_class['hour']} | {gym_class['day']}"
            )

            confirm_url(
                page,
                "https://sistemaplanbienestar.deportescompensar.com/entrenamiento/reserva/practica/libre",
            )

            try:

                with_recovery(
                    lambda: open_plan_and_use_membership(page),
                    page,
                    f"Usando memebresía para clase '{gym_class['name']}'",
                )

                if env.BOT_FORCE_RUN:
                    with_recovery(
                        lambda: select_by_day(page, gym_class["day"]),
                        page,
                        f"Seleccionando día {env.BOT_FORCE_RUN_DAY}' forzado",
                    )
                else:
                    with_recovery(
                        lambda: select_latest_date(page),
                        page,
                        f"Seleccionando día {gym_class['day']}",
                    )

                with_recovery(
                    lambda: gym_class_selector(
                        page, gym_class["name"], gym_class["hour"]
                    ),
                    page,
                    f"Seleccionando clase '{gym_class['name']}' en horario '{gym_class['hour']}'",
                )

                gym_class_confirmation(page)

                logger.success("🎉 Reserva completada")

                page.wait_for_timeout(1500)

                logger.success(f"✅ Reserva completada: {gym_class['name']}")

            except Exception as e:
                send_error_broadcast(
                    page, f"❌ Error reservando {gym_class['name']}: {e}"
                )

            # Esperar 60 segundos entre clases
            if index < len(classes) - 1:
                logger.info("⏳ Esperando 60 segundos para siguiente clase...")
                page.wait_for_timeout(60000)

        logger.success("🎉 Flujo completado")

    except Exception as e:
        send_error_broadcast(page, f"❌ Error general durante la ejecución: {e}")
    finally:
        try:
            logout(page)
        except Exception as logout_error:
            logger.warning(f"Error en logout: {logout_error}")

        try:
            context.close()
            playwright.stop()
        except:
            pass


if __name__ == "__main__":
    main()
