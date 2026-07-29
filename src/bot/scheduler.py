"""Determine which gym classes to book in the current cycle."""

from __future__ import annotations

from datetime import datetime

import pytz

from src.types.config import ExecutionConfig, ScheduleConfig, ScheduledClass
from src.utils.exceptions import ScheduleConfigError
from src.utils.logger import logger
from src.utils.time_utils import days_mapper, parse_start_hour


class Scheduler:
    """
    Decide which classes to attempt booking for the current time window.

    Supports two modes:
    - regular: matches today's schedule against `schedule.yaml`.
    - forced: uses the `bot_force_run` / `forcedClass` config for testing.
    """

    def __init__(self, schedule_config: ScheduleConfig, execution_config: ExecutionConfig) -> None:
        self._schedule = schedule_config
        self._execution = execution_config
        self._tz = pytz.timezone(schedule_config.timezone or "UTC")

    def get_classes(self) -> list[ScheduledClass]:
        """Entry point: decide between force-run and regular modes."""
        if self._execution.bot_force_run:
            return self._force_run_classes()
        return self._regular_run_classes()

    def _force_run_classes(self) -> list[ScheduledClass]:
        logger.warning("⚠️ → BOT_FORCE_RUN active ⚠️")
        forced = self._schedule.forcedClass

        if not forced or not all([forced.name, forced.hour, forced.day]):
            raise ScheduleConfigError(
                "❌ → BOT_FORCE_RUN active but 'forcedClass' in schedule is incomplete."
            )

        return [forced]

    def _regular_run_classes(self) -> list[ScheduledClass]:
        # Reservations open 2 days before the class — hence the offset.
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
                    hour, minute = parse_start_hour(gym_class.hour)
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
