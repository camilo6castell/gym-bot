"""Machine suspend/wake cycle management between reservation windows."""

from __future__ import annotations

import datetime
import time

from src.os_integration.os_integration_utils import (
    ReservationScheduleCalculator,
    SystemPowerController,
)
from src.types.config import PowerAutonomousConfig
from src.utils.logger import logger

_TIME_FORMAT = "%H:%M %d/%m"


class PowerCycleManager:
    """
    Orchestrate the autonomous power cycle: calculate the next reservation,
    decide whether to suspend or wait, and delegate to `SystemPowerController`
    to execute the suspend.
    """

    def __init__(
        self,
        schedule_calculator: ReservationScheduleCalculator,
        power_controller: SystemPowerController,
        power_config: PowerAutonomousConfig,
    ) -> None:
        self._schedule_calculator = schedule_calculator
        self._power_controller = power_controller
        self._power_config = power_config

    def run_suspend_now(self) -> None:
        """
        Program the wake alarm for the next reservation and suspend immediately.
        Usage: python -m src.main suspend-now
        """
        next_reservation = self._schedule_calculator.find_next_reservation()
        if not next_reservation:
            logger.info("📭 → No hay próximas reservas. No se programa suspensión.")
            return

        wake_time = self.calculate_wake_time(next_reservation)

        logger.info(f"📅 → Next reservation:\t\t\t{next_reservation.strftime(_TIME_FORMAT)}")
        logger.info(f"⏰ → Programming wake for:\t   {wake_time.strftime(_TIME_FORMAT)}")

        self._power_controller.set_wake_alarm(wake_time)
        logger.info("💤 → Suspending...")
        self._power_controller.suspend()

    def run_power_cycle(self) -> None:
        """
        Manage the full power cycle: active window → suspend → next cycle.
        Usage: python -m src.main power-cycle
        """
        next_reservation = self._schedule_calculator.find_next_reservation()
        if not next_reservation:
            logger.info("📭 → No hay próximas reservas.")
            return

        wake_time = self.calculate_wake_time(next_reservation)
        sleep_time = next_reservation + datetime.timedelta(
            minutes=self._power_config.sleep_minutes_after
        )
        now = self._schedule_calculator.get_now()

        logger.info(f"🕐 → Now:\t\t\t\t\t\t{now.strftime(_TIME_FORMAT)}")
        logger.info(f"⏰ → Wake scheduled:\t\t   {wake_time.strftime(_TIME_FORMAT)}")
        logger.info(f"💤 → Sleep after:\t\t\t{sleep_time.strftime(_TIME_FORMAT)}")

        if not (wake_time <= now <= sleep_time):
            logger.info("⏸️ → Outside active window. No suspension.")
            return

        self.wait_for_window_activation(now, sleep_time)

        logger.info("🔄 → Window ended. Scheduling next cycle.")
        next_reservation = self._schedule_calculator.find_next_reservation()
        if not next_reservation:
            logger.info("📭 → No more reservations.")
            return

        next_wake = self.calculate_wake_time(next_reservation)
        self._power_controller.set_wake_alarm(next_wake)
        logger.info(f"💤 → Suspending until: {next_wake.strftime(_TIME_FORMAT)}")
        self._power_controller.suspend()

    def calculate_wake_time(self, next_reservation: datetime.datetime) -> datetime.datetime:
        """Calculate the wake alarm time with a safety margin."""
        wake_minutes = self._power_config.wake_minutes_before
        return next_reservation - datetime.timedelta(minutes=wake_minutes)

    def wait_for_window_activation(
        self, now: datetime.datetime, sleep_time: datetime.datetime
    ) -> None:
        """Wait until the end of the active window."""
        remaining = max(0, (sleep_time - now).total_seconds())
        logger.info(f"⏳ Waiting {remaining:.0f} seconds until end of window")
        time.sleep(remaining)
