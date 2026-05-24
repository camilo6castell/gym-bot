import time
import datetime
from src.os_integration.os_integration_utils import (
    get_now,
    find_next_reservation,
    set_wake_alarm,
    suspend,
)
from src.config.config import Config
from src.utils.logger import logger

_config = Config()
_power = _config.get("APP_CONFIG").get("power_autonomous", {})
_time_format = "%H:%M %d/%m"


def run_suspend_now() -> None:
    """
    Programa el wake alarm para la próxima reserva y suspende inmediatamente.
    Uso: python -m src.main suspend-now
    """
    next_reservation = find_next_reservation()
    if not next_reservation:
        logger.info("📭 → No hay próximas reservas. No se programa suspensión.")
        return

    wake_time = calculate_wake_time(next_reservation)

    logger.info(f"📅 → Próxima reserva: {next_reservation.strftime(_time_format)}")
    logger.info(f"⏰ → Programando wake para: {wake_time.strftime(_time_format)}")

    set_wake_alarm(wake_time)
    logger.info("💤 → Suspendiendo...")
    suspend()


def run_power_cycle() -> None:
    """
    Gestiona el ciclo completo de power: ventana activa → suspensión → siguiente ciclo.
    Uso: python -m src.main power-cycle
    """
    next_reservation = find_next_reservation()
    if not next_reservation:
        logger.info("📭 → No hay próximas reservas.")
        return

    wake_time = calculate_wake_time(next_reservation)
    sleep_time = next_reservation + datetime.timedelta(
        minutes=_power.get("sleep_minutes_after", 10)
    )
    now = get_now()

    logger.info(f"🕐 → Ahora: {now.strftime(_time_format)}")
    logger.info(f"⏰ → Wake programado: {wake_time.strftime(_time_format)}")
    logger.info(f"💤 → Sleep después de: {sleep_time.strftime(_time_format)}")

    if wake_time <= now <= sleep_time:
        wait_for_window_activation(now, sleep_time)

        logger.info("🔄 → Ventana terminada. Programando siguiente ciclo.")
        next_reservation = find_next_reservation()
        if not next_reservation:
            logger.info("📭 → No hay más reservas.")
            return

        next_wake = calculate_wake_time(next_reservation)
        set_wake_alarm(next_wake)
        logger.info(f"💤 → Suspendiendo hasta: {next_wake.strftime(_time_format)}")
        suspend()
    else:
        logger.info("⏸️ → Fuera de ventana activa. Sin suspensión.")


def calculate_wake_time(next_reservation: datetime.datetime) -> datetime.datetime:
    """Calcular tiempo de wake alarm con margen de seguridad"""
    wake_minutes = _power.get("wake_minutes_before", 2)
    return next_reservation - datetime.timedelta(minutes=wake_minutes)


def wait_for_window_activation(
    now: datetime.datetime, sleep_time: datetime.datetime
) -> None:
    """Esperar hasta el final de la ventana activa"""
    remaining = max(0, (sleep_time - now).total_seconds())
    logger.info(f"⏳ Esperando {remaining:.0f} segundos hasta el final de la ventana")
    time.sleep(remaining)
