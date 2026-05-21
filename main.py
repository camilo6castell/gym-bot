from bot.browser import launch_chromium
from components.login_handler import perform_login
from components.logout_handler import perform_logout
from components.post_login_handler import perform_post_login
from components.reserve_gym_class_process_handler import perform_reserve_gym_class

from utils.error_broadcast import send_error_broadcast
import asyncio
from utils.logger import logger
from utils.recovery import with_recovery, with_soft_recovery
from utils.time_utils import spanish_day_mapper
from utils.element_utils import str_normalizer
from typing import cast
from playwright._impl._page import Page as ImplPage

from bot.bot_run import get_classes


def main():

    # Obtener clases — la lógica force/regular ya está en get_classes
    tentative_classes = get_classes()

    if not tentative_classes:
        # logger.info("📭 No hay clases para ejecutar en este momento.")
        return

    playwright, context, page = launch_chromium()

    try:

        with_recovery(
            lambda: perform_login(page),
            page,
            "Proceso de login",
        )

        with_soft_recovery(
            lambda: perform_post_login(page),
            page,
            "Flujo post-login",
        )

        logger.info(f"🥁 → Iniciando iteraciones de clases.")

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
                        spanish_day_name,
                        gym_class["name"],
                        gym_class["hour"],
                    ),
                    page,
                    f"Reservando '{gym_class['name']}' | {spanish_day_name}",
                )

            except Exception as e:
                page_for_broadcast = cast(ImplPage, getattr(page, "_impl_obj"))
                asyncio.run(
                    send_error_broadcast(
                        page_for_broadcast,
                        f"❌ → Error reservando {gym_class['name']}: {e}",
                    )
                )

            if index < len(tentative_classes) - 1:
                logger.info("⏳ → Esperando 60 segundos para siguiente clase...")
                page.wait_for_timeout(60000)

        logger.success("🏁 → Flujo completado")

    except Exception as e:
        # send_error_broadcast is async and expects the underlying Playwright impl Page
        try:
            page_for_broadcast = cast(ImplPage, getattr(page, "_impl_obj"))
            asyncio.run(
                send_error_broadcast(
                    page_for_broadcast, f"❌ → Error general durante la ejecución: {e}"
                )
            )
        except Exception:
            pass
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
