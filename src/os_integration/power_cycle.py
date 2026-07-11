"""Gestión del ciclo de suspensión/despertar de la máquina entre reservas."""

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
    Orquesta el ciclo de energía autónomo: calcula la próxima reserva,
    decide si corresponde suspender o esperar, y delega en
    `SystemPowerController` para ejecutar la suspensión.
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
        Programa el wake alarm para la próxima reserva y suspende inmediatamente.
        Uso: python -m src.main suspend-now
        """
        next_reservation = self._schedule_calculator.find_next_reservation()
        if not next_reservation:
            logger.info("📭 → No hay próximas reservas. No se programa suspensión.")
            return

        wake_time = self.calculate_wake_time(next_reservation)

        logger.info(f"📅 → Próxima reserva:\t\t\t {next_reservation.strftime(_TIME_FORMAT)}")
        logger.info(f"⏰ → Programando wake para:\t\t{wake_time.strftime(_TIME_FORMAT)}")

        self._power_controller.set_wake_alarm(wake_time)
        logger.info("💤 → Suspendiendo...")
        self._power_controller.suspend()

    def run_power_cycle(self) -> None:
        """
        Gestiona el ciclo completo de power: ventana activa → suspensión → siguiente ciclo.
        Uso: python -m src.main power-cycle
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

        logger.info(f"🕐 → Ahora:\t\t\t\t {now.strftime(_TIME_FORMAT)}")
        logger.info(f"⏰ → Wake programado:\t{wake_time.strftime(_TIME_FORMAT)}")
        logger.info(f"💤 → Sleep después de:\t {sleep_time.strftime(_TIME_FORMAT)}")

        if not (wake_time <= now <= sleep_time):
            logger.info("⏸️ → Fuera de ventana activa. Sin suspensión.")
            return

        self.wait_for_window_activation(now, sleep_time)

        logger.info("🔄 → Ventana terminada. Programando siguiente ciclo.")
        next_reservation = self._schedule_calculator.find_next_reservation()
        if not next_reservation:
            logger.info("📭 → No hay más reservas.")
            return

        next_wake = self.calculate_wake_time(next_reservation)
        self._power_controller.set_wake_alarm(next_wake)
        logger.info(f"💤 → Suspendiendo hasta: {next_wake.strftime(_TIME_FORMAT)}")
        self._power_controller.suspend()

    def calculate_wake_time(self, next_reservation: datetime.datetime) -> datetime.datetime:
        """Calcula el tiempo de wake alarm con margen de seguridad."""
        wake_minutes = self._power_config.wake_minutes_before
        return next_reservation - datetime.timedelta(minutes=wake_minutes)

    def wait_for_window_activation(
        self, now: datetime.datetime, sleep_time: datetime.datetime
    ) -> None:
        """Espera hasta el final de la ventana activa."""
        remaining = max(0, (sleep_time - now).total_seconds())
        logger.info(f"⏳ Esperando {remaining:.0f} segundos hasta el final de la ventana")
        time.sleep(remaining)
