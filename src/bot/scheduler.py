"""Cálculo de qué clases de gimnasio deben reservarse en el ciclo actual."""

from __future__ import annotations

from datetime import datetime

import pytz

from src.types.config import ExecutionConfig, ScheduleConfig, ScheduledClass
from src.utils.exceptions import ScheduleConfigError
from src.utils.logger import logger
from src.utils.time_utils import days_mapper


class Scheduler:
    """
    Determina, para el momento actual, qué clases de gimnasio corresponde
    intentar reservar — ya sea en modo normal (según `schedule.yaml`) o en
    modo forzado (`bot_force_run`, útil para pruebas y ejecución manual).
    """

    def __init__(self, schedule_config: ScheduleConfig, execution_config: ExecutionConfig) -> None:
        self._schedule = schedule_config
        self._execution = execution_config
        self._tz = pytz.timezone(schedule_config.timezone or "UTC")

    def get_classes(self) -> list[ScheduledClass]:
        """Punto de entrada: decide entre modo forzado y modo regular."""
        if self._execution.bot_force_run:
            return self._force_run_classes()
        return self._regular_run_classes()

    def _force_run_classes(self) -> list[ScheduledClass]:
        logger.warning("⚠️ → BOT_FORCE_RUN activo ⚠️")
        forced = self._schedule.forcedClass

        if not forced or not all([forced.name, forced.hour, forced.day]):
            raise ScheduleConfigError(
                "❌ → BOT_FORCE_RUN activo pero faltan datos en 'forcedClass' del schedule."
            )

        return [forced]

    def _regular_run_classes(self) -> list[ScheduledClass]:
        # Las reservas abren 2 días antes de la clase — de ahí el offset.
        now = datetime.now(self._tz)
        target_weekday = (now.weekday() - 2) % 7
        scheduled_classes: list[ScheduledClass] = []

        for day_name, day_classes in self._schedule.days.items():
            if days_mapper(day_name) != target_weekday:
                continue
            if not day_classes:
                continue

            for gym_class in day_classes:
                try:
                    start_hour = gym_class.hour.split(" - ")[0]
                    hour, minute = map(int, start_hour.split(":"))
                except (ValueError, IndexError):
                    continue

                activation_hour, activation_minute = self._apply_execution_adjustment(hour, minute)

                if now.hour == activation_hour and now.minute == activation_minute:
                    scheduled_classes.append(
                        ScheduledClass(name=gym_class.name, hour=gym_class.hour, day=day_name)
                    )

        return scheduled_classes

    def _apply_execution_adjustment(self, hour: int, minute: int) -> tuple[int, int]:
        adjustment = self._execution.execution_adjustment
        if adjustment == 0:
            return hour, minute

        minute += adjustment
        if minute < 0:
            hour -= 1
            minute += 60
        elif minute >= 60:
            hour += 1
            minute -= 60

        hour = hour % 24
        return hour, minute
