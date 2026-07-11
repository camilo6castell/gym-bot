"""
Utilidades de integración con el sistema operativo.

Separadas en dos responsabilidades:
  - `ReservationScheduleCalculator`: sabe cuándo es la próxima reserva.
  - `SystemPowerController`: sabe cómo dormir/despertar la máquina.

Ninguna de las dos conoce a la otra — `PowerCycleManager` (en power_cycle.py)
es quien las combina.
"""

from __future__ import annotations

import datetime
import subprocess
from zoneinfo import ZoneInfo

from src.types.config import PowerAutonomousConfig, ScheduleConfig
from src.utils.logger import logger
from src.utils.time_utils import days_mapper


class ReservationScheduleCalculator:
    """Calcula la fecha/hora de la próxima reserva programada según `schedule.yaml`."""

    def __init__(self, schedule_config: ScheduleConfig) -> None:
        self._schedule = schedule_config
        self._tz = ZoneInfo(schedule_config.timezone or "UTC")

    def get_now(self) -> datetime.datetime:
        """Hora actual en la zona horaria configurada."""
        return datetime.datetime.now(self._tz)

    def find_next_reservation(self) -> datetime.datetime | None:
        """Devuelve la fecha/hora de la próxima clase programada, o `None` si no hay ninguna."""
        now = self.get_now()
        upcoming: list[datetime.datetime] = []

        for day_name, gym_classes in self._schedule.days.items():
            reservation_weekday = (days_mapper(day_name) + 2) % 7

            for gym_class in gym_classes:
                try:
                    start_hour = gym_class.hour.split(" - ")[0]
                    hour, minute = map(int, start_hour.split(":"))
                except (ValueError, IndexError):
                    continue

                days_ahead = (reservation_weekday - now.weekday()) % 7
                reservation_date = (now + datetime.timedelta(days=days_ahead)).replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )

                if reservation_date <= now:
                    reservation_date += datetime.timedelta(days=7)

                upcoming.append(reservation_date)

        return min(upcoming) if upcoming else None


class SystemPowerController:
    """Controla la suspensión y el wake alarm del sistema (Linux / RTC)."""

    def __init__(self, power_config: PowerAutonomousConfig) -> None:
        self._power_config = power_config

    def set_wake_alarm(self, dt: datetime.datetime) -> None:
        """Programa el wake alarm de RTC para la fecha/hora indicada."""
        wakealarm_path = self._power_config.wakealarm_path
        if not wakealarm_path:
            logger.warning("⚠️ → wakealarm_path no configurado, no se puede programar wake alarm.")
            return

        timestamp = int(dt.timestamp())
        with open(wakealarm_path, "w") as f:
            f.write("0")
        with open(wakealarm_path, "w") as f:
            f.write(str(timestamp))

    def suspend(self) -> None:
        """Suspende el sistema con manejo de errores."""
        try:
            subprocess.run(["/usr/bin/sudo", "-n", "/usr/bin/systemctl", "suspend"], check=True)
        except Exception as e:
            logger.error(f"❌ Error al suspender: {e}", exc_info=True)
            raise
