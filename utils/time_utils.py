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
        raise RuntimeError(f"Día inválido: {day}")


def spanish_day_mapper(day: str) -> str:
    if day.lower() in SPANISH_DAYS_MAP:
        return SPANISH_DAYS_MAP[day.lower()]
    else:
        raise RuntimeError(f"Día inválido: {day}")


# TIME


def military_time_range_to_ampm(military_range: str) -> str:
    """
    Convierte rango de hora militar a AM/PM.
    '07:00 - 08:00' → '07:00 AM - 08:00 AM'
    """
    parts = military_range.split(" - ")
    if len(parts) != 2:
        raise ValueError(f"Formato de hora inválido: '{military_range}'")

    return f"{_convert_military_time_to_ampm(parts[0])} - {_convert_military_time_to_ampm(parts[1])}"


def _convert_military_time_to_ampm(time_str: str) -> str:
    hour, minute = map(int, time_str.strip().split(":"))
    period = "AM" if hour < 12 else "PM"
    display_hour = hour if hour <= 12 else hour - 12
    display_hour = 12 if display_hour == 0 else display_hour
    return f"{display_hour:02d}:{minute:02d} {period}"
