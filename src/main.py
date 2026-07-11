"""
Punto de entrada de gym-bot.

Todas las dependencias se construyen aquí, a partir de una única instancia
de `Settings`, y se inyectan explícitamente en cada clase que las necesita.
Ningún componente crea sus propias dependencias ni lee configuración global.
"""

import argparse

from src.notifications.telegram import TelegramClient
from src.settings.provider import Settings
from src.types.config import ScheduledClass
from src.utils.logger import logger


def run_bot(settings: Settings) -> None:
    """Flujo principal de reserva de clases."""
    from src.bot.browser import Browser
    from src.bot.scheduler import Scheduler
    from src.components.day_selector import DateSelector
    from src.components.gym_class_acceptance import ClassAcceptance
    from src.components.gym_class_booker import ClassBooker
    from src.components.gym_class_checker import ClassChecker
    from src.components.login import LoginPage
    from src.components.logout import LogoutPage
    from src.components.membership import MembershipSelector
    from src.components.post_login import PostLoginPage
    from src.components.reserve_process import ReservationProcess
    from src.utils.error_broadcast import ErrorBroadcaster
    from src.utils.recovery import Recovery
    from src.utils.time_utils import spanish_day_mapper, wait_until_reservation_opens

    notifier: TelegramClient = TelegramClient(settings.env.TOKEN, settings.env.CHAT_ID)
    recovery: Recovery = Recovery(notifier)
    error_broadcaster: ErrorBroadcaster = ErrorBroadcaster(notifier)

    scheduler = Scheduler(settings.schedule, settings.app_config.execution)
    tentative_classes = scheduler.get_classes()
    if not tentative_classes:
        return

    browser = Browser(
        os_config=settings.app_config.os,
        execution_config=settings.app_config.execution,
        chromium_profile_path=settings.chromium_profile_path,
        firefox_profile_path=settings.firefox_profile_path,
    )
    _playwright, _context, page = browser.launch_chromium()

    login_page = LoginPage(
        env_config=settings.app_config.environment,
        selectors_config=settings.app_config.selectors,
        recovery=recovery,
        doc_type=settings.env.COMPENSAR_DOC_TYPE,
        doc_num=settings.env.COMPENSAR_DOC_NUM,
        password=settings.env.COMPENSAR_PASSWORD,
    )
    post_login_page = PostLoginPage(
        env_config=settings.app_config.environment,
        selectors_config=settings.app_config.selectors,
        recovery=recovery,
    )
    date_selector = DateSelector(recovery)
    membership_selector = MembershipSelector(recovery)
    class_acceptance = ClassAcceptance(recovery)
    class_checker = ClassChecker(recovery)
    class_booker = ClassBooker(class_acceptance, class_checker, recovery)
    reservation_process = ReservationProcess(
        env_config=settings.app_config.environment,
        execution_config=settings.app_config.execution,
        date_selector=date_selector,
        membership_selector=membership_selector,
        class_booker=class_booker,
    )
    logout_page = LogoutPage(recovery)

    recovery.set_batch_classes([c.model_dump() for c in tentative_classes])

    recovery.with_recovery(lambda: login_page.perform_login(page), page, "Proceso de login")
    recovery.with_recovery(
        lambda: post_login_page.perform_post_login(page), page, "Flujo post-login"
    )

    try:
        logger.info("🥁 → Iniciando iteraciones de clases.")

        for index, gym_class in enumerate(tentative_classes):
            spanish_day_name = spanish_day_mapper(gym_class.day)
            logger.info(
                f"🎯 → Clase {index + 1}/{len(tentative_classes)}: "
                f"{gym_class.name} | {gym_class.hour} | {spanish_day_name}"
            )

            wait_until_reservation_opens(gym_class.hour)

            def _reserve_current_class(
                gym_class: ScheduledClass = gym_class,
                spanish_day_name: str = spanish_day_name,
            ) -> None:
                reservation_process.reserve(
                    page,
                    spanish_day_name,
                    gym_class.name,
                    gym_class.hour,
                )

            try:
                recovery.with_recovery(
                    _reserve_current_class,
                    page,
                    f"Reservando '{gym_class.name}' | {spanish_day_name}",
                )
            except Exception as e:
                error_broadcaster.send(page, f"❌ → Error reservando {gym_class.name}: {e}")

            if index < len(tentative_classes) - 1:
                logger.info("⏳ → Esperando 10 segundos para siguiente clase...")
                page.wait_for_timeout(10000)

        logger.success("🏁 → Flujo completado")

    except Exception as e:
        error_broadcaster.send(page, f"❌ → Error general: {e}")
    finally:
        try:
            logout_page.perform_logout(page)
        except Exception as e:
            logger.warning(f"⚠️ → Error en logout: {e}")
        browser.close()


def main() -> None:
    settings = Settings()
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
        from src.os_integration.os_integration_utils import (
            ReservationScheduleCalculator,
            SystemPowerController,
        )
        from src.os_integration.power_cycle import PowerCycleManager

        power_cycle_manager = PowerCycleManager(
            schedule_calculator=ReservationScheduleCalculator(settings.schedule),
            power_controller=SystemPowerController(settings.app_config.power_autonomous),
            power_config=settings.app_config.power_autonomous,
        )
        power_cycle_manager.run_suspend_now()

    elif args.command == "power-cycle":
        from filelock import FileLock

        from src.os_integration.os_integration_utils import (
            ReservationScheduleCalculator,
            SystemPowerController,
        )
        from src.os_integration.power_cycle import PowerCycleManager

        power_cycle_manager = PowerCycleManager(
            schedule_calculator=ReservationScheduleCalculator(settings.schedule),
            power_controller=SystemPowerController(settings.app_config.power_autonomous),
            power_config=settings.app_config.power_autonomous,
        )
        lock: FileLock = FileLock("/tmp/gym-bot-power-cycle.lock")

        with lock:
            power_cycle_manager.run_power_cycle()

    else:
        # default: sin subcomando o "run" → flujo de reserva
        run_bot(settings=settings)


if __name__ == "__main__":
    main()
