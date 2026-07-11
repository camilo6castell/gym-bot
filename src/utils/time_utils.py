"""Utilidades de manejo de fechas, horas y días de la semana."""

from __future__ import annotations

import time
from datetime import datetime

from src.utils.logger import logger

DAYS_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

SPANISH_DAYS_MAP = {
    "monday": "lunes",
    "tuesday": "martes",
    "wednesday": "miercoles",
    "thursday": "jueves",
    "friday": "viernes",
    "saturday": "sabado",
    "sunday": "domingo",
}

# DAYS


def days_mapper(day: str) -> int:
    if day.lower() in DAYS_MAP:
        return DAYS_MAP[day.lower()]
    else:
        raise ValueError(f"Día inválido: {day}")


def spanish_day_mapper(day: str) -> str:
    if day.lower() in SPANISH_DAYS_MAP:
        return SPANISH_DAYS_MAP[day.lower()]
    else:
        raise ValueError(f"Día inválido: {day}")


# TIME


def wait_until_reservation_opens(gym_class_hour: str) -> None:
    """Espera hasta 1 segundo después de la hora de apertura de reserva."""
    # gym_class_hour viene como "07:00 - 08:00", extraemos "07:00"
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
        logger.info(f"⏳ → Esperando {wait_seconds:.1f}s hasta {target.strftime('%H:%M:%S')}")
        time.sleep(wait_seconds)
    else:
        logger.info(
            f"✅ → Ya pasó la hora de apertura ({target.strftime('%H:%M:%S')}), continuando"
        )


def military_time_range_to_ampm(military_range: str) -> str:
    """
    Convierte rango de hora militar a AM/PM.
    '07:00 - 08:00' → '07:00 AM - 08:00 AM'
    """
    parts = military_range.split(" - ")
    if len(parts) != 2:
        raise ValueError(f"Formato de hora inválido: '{military_range}'")

    start_ampm = _convert_military_time_to_ampm(parts[0])
    end_ampm = _convert_military_time_to_ampm(parts[1])
    return f"{start_ampm} - {end_ampm}"


def _convert_military_time_to_ampm(time_str: str) -> str:
    hour, minute = map(int, time_str.strip().split(":"))
    period = "AM" if hour < 12 else "PM"
    display_hour = hour if hour <= 12 else hour - 12
    display_hour = 12 if display_hour == 0 else display_hour
    return f"{display_hour:02d}:{minute:02d} {period}"
