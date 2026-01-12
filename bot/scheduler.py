from typing import Optional, Dict, Any
import yaml
from datetime import datetime, timedelta
import pytz


DAYS_MAP = {
    "lunes": 0,
    "martes": 1,
    "miércoles": 2,
    "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sábado": 5,
    "sabado": 5,
    "domingo": 6,
}


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_next_class_for_testing(config):
    """
    Devuelve la primera clase futura disponible,
    sin importar horario de activación.
    """
    tz = pytz.timezone(config["timezone"])
    now = datetime.now(tz)

    upcoming = []

    for day_name, clases in config["dias"].items():
        target_weekday = DAYS_MAP[day_name.lower()]

        for clase in clases:
            start_hour = clase["hora"].split(" - ")[0]
            hour, minute = map(int, start_hour.split(":"))

            days_ahead = (target_weekday - now.weekday()) % 7
            target_date = now.date() + timedelta(days=days_ahead)

            class_dt = tz.localize(
                datetime(
                    target_date.year,
                    target_date.month,
                    target_date.day,
                    hour,
                    minute,
                )
            )

            if class_dt >= now:
                upcoming.append((class_dt, clase))

    if not upcoming:
        return None

    # devolver la más cercana
    upcoming.sort(key=lambda x: x[0])
    return upcoming[0][1]


def should_run_now(
    config_path="config/classes.yaml", force=False
) -> Optional[Dict[str, Any]]:
    config = load_config(config_path)
    tz = pytz.timezone(config["timezone"])
    now = datetime.now(tz)

    if force:
        return get_next_class_for_testing(config)

    for day_name, clases in config["dias"].items():
        target_weekday = DAYS_MAP[day_name.lower()]

        for clase in clases:
            start_hour = clase["hora"].split(" - ")[0]
            hour, minute = map(int, start_hour.split(":"))

            days_ahead = (target_weekday - now.weekday()) % 7
            target_date = now.date() + timedelta(days=days_ahead)

            activation_dt = (
                tz.localize(
                    datetime(
                        target_date.year,
                        target_date.month,
                        target_date.day,
                        hour,
                        minute,
                    )
                )
                - timedelta(days=2)
                + timedelta(minutes=1)
            )

            if abs((now - activation_dt).total_seconds()) < 60:
                return clase

    return None
