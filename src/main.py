import argparse

from src.notifications.telegram import TelegramClient
from src.settings.provider import Settings
from src.utils.logger import logger

settings: Settings = Settings()
notifier: TelegramClient = TelegramClient(
    settings.get("TELEGRAM_TOKEN"), settings.get("TELEGRAM_CHAT_ID")
)


def run_bot() -> None:
    """Flujo principal de reserva de clases."""
    from src.bot.browser import launch_chromium
    from src.bot.scheduler import get_classes
    from src.components.login import perform_login
    from src.components.logout import perform_logout
    from src.components.post_login import perform_post_login
    from src.components.reserve_process import perform_reserve_gym_class
    from src.utils.error_broadcast import send_error_broadcast
    from src.utils.recovery import recovery
    from src.utils.strings import str_normalizer
    from src.utils.time_utils import spanish_day_mapper, wait_until_reservation_opens

    tentative_classes = get_classes()
    if not tentative_classes:
        return

    playwright, context, page = launch_chromium()

    recovery.set_batch_classes(tentative_classes)

    recovery.with_recovery(lambda: perform_login(page), page, "Proceso de login")
    recovery.with_recovery(lambda: perform_post_login(page), page, "Flujo post-login")

    try:
        logger.info("🥁 → Iniciando iteraciones de clases.")

        for index, gym_class in enumerate(tentative_classes):
            spanish_day_name = spanish_day_mapper(str_normalizer(gym_class["day"]))
            logger.info(
                f"🎯 → Clase {index + 1}/{len(tentative_classes)}: "
                f"{gym_class['name']} | {gym_class['hour']} | {spanish_day_name}"
            )

            wait_until_reservation_opens(gym_class["hour"])

            try:
                recovery.with_recovery(
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
                send_error_broadcast(page, f"❌ → Error reservando {gym_class['name']}: {e}")

            if index < len(tentative_classes) - 1:
                logger.info("⏳ → Esperando 10 segundos para siguiente clase...")
                page.wait_for_timeout(10000)

        logger.success("🏁 → Flujo completado")

    except Exception as e:
        send_error_broadcast(page, f"❌ → Error general: {e}")
    finally:
        try:
            perform_logout(page)
        except Exception as e:
            logger.warning(f"⚠️ → Error en logout: {e}")
        try:
            context.close()
            playwright.stop()
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="gym-bot", description="Bot de reservas de gimnasio con integración OS"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Subcomando por defecto — reservar clases
    subparsers.add_parser("run", help="Ejecutar flujo de reserva (default)")

    # Subcomandos de power management
    subparsers.add_parser("suspend-now", help="Programar wake alarm y suspender inmediatamente")
    subparsers.add_parser(
        "power-cycle",
        help="Gestionar ciclo completo de power (ventana activa → suspensión)",
    )

    args = parser.parse_args()

    if args.command == "suspend-now":
        from src.os_integration.power_cycle import run_suspend_now

        run_suspend_now()

    elif args.command == "power-cycle":
        from filelock import FileLock

        from src.os_integration.power_cycle import run_power_cycle

        lock: FileLock = FileLock("/tmp/gym-bot-power-cycle.lock")

        with lock:
            run_power_cycle()

    else:
        # default: sin subcomando o "run" → flujo de reserva
        run_bot()


if __name__ == "__main__":
    main()
