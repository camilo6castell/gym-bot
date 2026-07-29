"""Tests for the Scheduler class."""

from __future__ import annotations

from typing import cast

import pytest

from src.bot.scheduler import Scheduler
from src.types.config import ExecutionConfig, GymClass, ScheduleConfig, ScheduledClass, Weekday


def _make_schedule_config(
    timezone: str = "America/Bogota",
    forced_day: str | None = None,
) -> ScheduleConfig:
    days: dict[Weekday, list[GymClass]] = {
        "monday": [GymClass(name="Pilates", hour="06:00 - 07:00")],
        "tuesday": [GymClass(name="Yoga", hour="07:00 - 08:00")],
    }
    forced = (
        ScheduledClass(name="ForcedClass", hour="09:00 - 10:00", day=cast(Weekday, forced_day))
        if forced_day
        else None
    )
    return ScheduleConfig(timezone=timezone, days=days, forced_class=forced)


def _make_execution(force_run: bool = False, adjustment: int = 0) -> ExecutionConfig:
    return ExecutionConfig(
        bot_force_run=force_run,
        execution_adjustment=adjustment,
        bot_headless=True,
    )


class TestSchedulerForceRun:
    def test_force_run_returns_forced_class(self) -> None:
        schedule = _make_schedule_config(forced_day="monday")
        execution = _make_execution(force_run=True)
        scheduler = Scheduler(schedule, execution)

        classes = scheduler.get_classes()

        assert len(classes) == 1
        assert classes[0].name == "ForcedClass"
        assert classes[0].day == "monday"

    def test_force_run_missing_forced_class_raises_error(self) -> None:
        schedule = _make_schedule_config(forced_day=None)
        execution = _make_execution(force_run=True)
        scheduler = Scheduler(schedule, execution)

        with pytest.raises(ValueError):
            scheduler.get_classes()


class TestSchedulerApplyExecutionAdjustment:
    def test_zero_adjustment_returns_same(self) -> None:
        schedule = _make_schedule_config()
        execution = _make_execution(force_run=False, adjustment=0)
        scheduler = Scheduler(schedule, execution)

        result = scheduler._apply_execution_adjustment(7, 0)  # pyright: ignore[reportPrivateUsage]
        assert result == (7, 0)

    def test_negative_adjustment(self) -> None:
        schedule = _make_schedule_config()
        execution = _make_execution(force_run=False, adjustment=-1)
        scheduler = Scheduler(schedule, execution)

        result = scheduler._apply_execution_adjustment(7, 0)  # pyright: ignore[reportPrivateUsage]
        assert result == (6, 59)

    def test_positive_adjustment(self) -> None:
        schedule = _make_schedule_config()
        execution = _make_execution(force_run=False, adjustment=5)
        scheduler = Scheduler(schedule, execution)

        result = scheduler._apply_execution_adjustment(7, 0)  # pyright: ignore[reportPrivateUsage]
        assert result == (7, 5)

    def test_negative_adjustment_wraps_hour(self) -> None:
        schedule = _make_schedule_config()
        execution = _make_execution(force_run=False, adjustment=-5)
        scheduler = Scheduler(schedule, execution)

        result = scheduler._apply_execution_adjustment(7, 2)  # pyright: ignore[reportPrivateUsage]
        assert result == (6, 57)

    def test_positive_adjustment_wraps_hour(self) -> None:
        schedule = _make_schedule_config()
        execution = _make_execution(force_run=False, adjustment=5)
        scheduler = Scheduler(schedule, execution)

        result = scheduler._apply_execution_adjustment(7, 58)  # pyright: ignore[reportPrivateUsage]
        assert result == (8, 3)

    def test_midnight_wraparound(self) -> None:
        schedule = _make_schedule_config()
        execution = _make_execution(force_run=False, adjustment=-1)
        scheduler = Scheduler(schedule, execution)

        result = scheduler._apply_execution_adjustment(0, 0)  # pyright: ignore[reportPrivateUsage]
        assert result == (23, 59)
