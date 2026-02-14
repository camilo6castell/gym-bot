from loguru import logger
from bot.browser import launch_browser
from bot.login import login
from bot.logout import logout
from bot.utils import handle_page_load
from bot.post_login_flow import run_post_login_flow
from bot.scheduler import should_run_now
import time
from bot.config import (
    BOT_FORCE_RUN,
    BOT_HEADLESS,
    BOT_FORCE_RUN_CLASS,
    BOT_FORCE_RUN_HOUR,
    BOT_FORCE_RUN_DAY,
)

def main():
    if BOT_FORCE_RUN:
        logger.warning("⚠️ BOT_FORCE_RUN activo – usando clase forzada")

        if not BOT_FORCE_RUN_CLASS or not BOT_FORCE_RUN_HOUR:
            raise ValueError(
                "BOT_FORCE_RUN activo pero faltan BOT_FORCE_RUN_CLASS o BOT_FORCE_RUN_HOUR"
            )

        clases = [{
            "nombre": BOT_FORCE_RUN_CLASS,
            "hora": BOT_FORCE_RUN_HOUR,
            "dia": BOT_FORCE_RUN_DAY,
        }]
    else:
        clases = should_run_now()
        if not clases:
            logger.info("⏰ No hay clases programadas para este momento")
            return

    playwright, browser, context, page = launch_browser(headless=BOT_HEADLESS)

    try:
        login(page)
        logger.success("✅ Login exitoso")

        for index, clase in enumerate(clases):
            logger.info(
                f"🎯 Intentando clase {index+1}/{len(clases)}: "
                f"{clase['nombre']} | {clase['hora']} | {clase.get('dia','*')}"
            )

            try:
                run_post_login_flow(page, clase)
                logger.success(f"✅ Reserva completada: {clase['nombre']}")

            except Exception as e:
                logger.error(f"❌ Error reservando {clase['nombre']}: {e}")

            # Esperar 60 segundos entre clases
            if index < len(clases) - 1:
                logger.info("⏳ Esperando 60 segundos para siguiente clase...")
                page.wait_for_timeout(60000)

        logger.success("🎉 Flujo completado")

    except Exception as e:
        logger.error(f"❌ Error general durante la ejecución: {e}")
        page.screenshot(path=f"error_{int(time.time())}.png")

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