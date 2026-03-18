def days_mapper(day: str) -> int:
    if day.lower() in DAYS_MAP:
        return DAYS_MAP[day.lower()]
    else:
        raise RuntimeError(f"Día inválido: {day}")


DAYS_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}
