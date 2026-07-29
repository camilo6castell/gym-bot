"""
OS integration utilities.

Split into two responsibilities:
  - `ReservationScheduleCalculator`: knows when the next reservation is.
  - `SystemPowerController`: knows how to suspend/wake the machine.

Neither knows about the other — `PowerCycleManager` (in power_cycle.py)
combines them.
"""

from __future__ import annotations

import datetime
import subprocess
from zoneinfo import ZoneInfo

from src.types.config import PowerAutonomousConfig, ScheduleConfig
from src.utils.logger import logger
from src.utils.time_utils import days_mapper, parse_start_hour


class ReservationScheduleCalculator:
    """Calculate the date/time of the next scheduled reservation from `schedule.yaml`."""

    def __init__(self, schedule_config: ScheduleConfig) -> None:
        self._schedule = schedule_config
        self._tz = ZoneInfo(schedule_config.timezone or "UTC")

    def get_now(self) -> datetime.datetime:
        """Current time in the configured timezone."""
        return datetime.datetime.now(self._tz)

    def find_next_reservation(self) -> datetime.datetime | None:
        """Return the next class reservation datetime, or None if none found."""
        now = self.get_now()
        upcoming: list[datetime.datetime] = []

        for day_name, gym_classes in self._schedule.days.items():
            reservation_weekday = (days_mapper(day_name) + 2) % 7

            for gym_class in gym_classes:
                try:
                    hour, minute = parse_start_hour(gym_class.hour)
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
    """Control system suspend and RTC wake alarm (Linux)."""

    def __init__(self, power_config: PowerAutonomousConfig) -> None:
        self._power_config = power_config

    def set_wake_alarm(self, dt: datetime.datetime) -> None:
        """Program the RTC wake alarm for the given datetime."""
        wakealarm_path = self._power_config.wakealarm_path
        if not wakealarm_path:
            logger.warning("⚠️ → wakealarm_path not configured, cannot set wake alarm.")
            return

        timestamp = int(dt.timestamp())
        with open(wakealarm_path, "w") as f:
            f.write("0")
        with open(wakealarm_path, "w") as f:
            f.write(str(timestamp))

    def suspend(self) -> None:
        """Suspend the system with error handling."""
        try:
            subprocess.run(["/usr/bin/sudo", "-n", "/usr/bin/systemctl", "suspend"], check=True)
        except Exception as e:
            logger.error(f"❌ Error suspending: {e}", exc_info=True)
            raise
