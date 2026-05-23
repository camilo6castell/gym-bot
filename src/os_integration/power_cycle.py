import time
import datetime
from src.os_integration.os_integration_utils import (
    get_now,
    find_next_reservation,
    set_wake_alarm,
    suspend,
)
from src.config.config import Config
from pathlib import Path
from src.utils.logger import logger

_config = Config(env_file=str(Path(__file__).resolve().parent.parent / ".env"))
_power = _config.get("APP_CONFIG").get("power_autonomous", {})


def run_suspend_now() -> None:
    """
    Programa el wake alarm para la próxima reserva y suspende inmediatamente.
    Equivalente al antiguo start_power_autonomous.py
    Uso: python -m src.main suspend-now
    """
    next_reservation = find_next_reservation()
    if not next_reservation:
        logger.info("📭 → No hay próximas reservas. No se programa suspensión.")
        return

    wake_time = next_reservation - datetime.timedelta(
        minutes=_power.get("wake_minutes_before", 2)
    )

    logger.info(f"📅 → Próxima reserva: {next_reservation}")
    logger.info(f"⏰ → Programando wake para: {wake_time}")

    set_wake_alarm(wake_time)
    logger.info("💤 → Suspendiendo...")
    suspend()


def run_power_cycle() -> None:
    """
    Gestiona el ciclo completo de power: ventana activa → suspensión → siguiente ciclo.
    Equivalente al antiguo power_autonomous.py
    Uso: python -m src.main power-cycle
    """
    next_reservation = find_next_reservation()
    if not next_reservation:
        logger.info("📭 → No hay próximas reservas.")
        return

    wake_time = next_reservation - datetime.timedelta(
        minutes=_power.get("wake_minutes_before", 2)
    )
    sleep_time = next_reservation + datetime.timedelta(
        minutes=_power.get("sleep_minutes_after", 10)
    )
    now = get_now()

    logger.info(f"🕐 → Ahora: {now}")
    logger.info(f"⏰ → Wake programado: {wake_time}")
    logger.info(f"💤 → Sleep después de: {sleep_time}")

    if wake_time <= now <= sleep_time:
        remaining = (sleep_time - now).total_seconds()
        logger.info(f"✅ → Dentro de ventana activa. Despierto por {remaining:.0f}s")
        time.sleep(max(0, remaining))

        logger.info("🔄 → Ventana terminada. Programando siguiente ciclo.")
        next_reservation = find_next_reservation()
        if not next_reservation:
            logger.info("📭 → No hay más reservas.")
            return

        next_wake = next_reservation - datetime.timedelta(
            minutes=_power.get("wake_minutes_before", 2)
        )
        set_wake_alarm(next_wake)
        logger.info(f"💤 → Suspendiendo hasta: {next_wake}")
        suspend()
    else:
        logger.info("⏸️ → Fuera de ventana activa. Sin suspensión.")
