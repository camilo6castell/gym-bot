"""Date, time, and weekday utility functions."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Final

from src.utils.logger import logger

DAYS_MAP: Final = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

SPANISH_DAYS_MAP: Final = {
    "monday": "lunes",
    "tuesday": "martes",
    "wednesday": "miercoles",
    "thursday": "jueves",
    "friday": "viernes",
    "saturday": "sabado",
    "sunday": "domingo",
}


def days_mapper(day: str) -> int:
    if day.lower() in DAYS_MAP:
        return DAYS_MAP[day.lower()]
    else:
        raise ValueError(f"Invalid day: {day}")


def spanish_day_mapper(day: str) -> str:
    if day.lower() in SPANISH_DAYS_MAP:
        return SPANISH_DAYS_MAP[day.lower()]
    else:
        raise ValueError(f"Invalid day: {day}")


def parse_start_hour(hour_range: str) -> tuple[int, int]:
    """Extract (hour, minute) from a time range string like '07:00 - 08:00'."""
    parts = hour_range.split(" - ")
    if not parts:
        raise ValueError(f"Invalid time range: '{hour_range}'")
    start = parts[0].strip()
    hour, minute = map(int, start.split(":"))
    return hour, minute


def wait_until_reservation_opens(gym_class_hour: str) -> None:
    """Wait until 1 second after the reservation opening time."""
    start_hour = gym_class_hour.split(" - ")[0].strip()
    now = datetime.now()
    target = now.replace(
        hour=int(start_hour.split(":")[0]),
        minute=int(start_hour.split(":")[1]),
        second=1,
        microsecond=0,
    )

    if now < target:
        wait_seconds = (target - now).total_seconds()
        logger.info(f"⏳ → Waiting {wait_seconds:.1f}s until {target.strftime('%H:%M:%S')}")
        time.sleep(wait_seconds)
    else:
        logger.info(
            f"✅ → Opening time ({target.strftime('%H:%M:%S')}) already passed, continuing"
        )


def military_time_range_to_ampm(military_range: str) -> str:
    """
    Convert military time range to AM/PM format.
    '07:00 - 08:00' → '07:00 AM - 08:00 AM'
    """
    parts = military_range.split(" - ")
    if len(parts) != 2:
        raise ValueError(f"Invalid time format: '{military_range}'")

    start_ampm = _convert_military_time_to_ampm(parts[0])
    end_ampm = _convert_military_time_to_ampm(parts[1])
    return f"{start_ampm} - {end_ampm}"


def _convert_military_time_to_ampm(time_str: str) -> str:
    hour, minute = map(int, time_str.strip().split(":"))
    period = "AM" if hour < 12 else "PM"
    display_hour = hour if hour <= 12 else hour - 12
    display_hour = 12 if display_hour == 0 else display_hour
    return f"{display_hour:02d}:{minute:02d} {period}"
