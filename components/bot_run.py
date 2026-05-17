import pytz
from core.config import Config
from datetime import datetime
from utils.time_utils import days_mapper
from utils.logger import logger
from components.add_a_minute_for_x import should_add_a_minute_for_x

config = Config(env_file=".env")
schedule = config.get("SCHEDULE")


def is_force_run() -> list[dict[str, str]]:
    logger.warning("⚠️  → BOT_FORCE_RUN activo ⚠️")

    forcedClass = schedule.get("forcedClass")

    if (
        not forcedClass.get("name")
        or not forcedClass.get("hour")
        or not forcedClass.get("day")
    ):
        raise ValueError(
            "❌ → Error BOT_FORCE_RUN activo pero faltan datos de clase forzada."
        )

    return [forcedClass]


def is_regular_run() -> list[dict[str, str]]:
    if not schedule or "days" not in schedule:
        return []

    # 🕒 Zona horaria segura
    timezone_str = schedule.get("timezone")
    tz = pytz.timezone(timezone_str)
    now = datetime.now(tz)

    # 🔥 Siempre 2 días atrás
    target_weekday = (now.weekday() - 2) % 7

    gym_classes: list[dict[str, str]] = []

    for day_name, day_classes in schedule.get("days", {}).items():

        if days_mapper(day_name) != target_weekday:
            continue

        if not day_classes:
            continue

        for gym_class in day_classes:
            try:
                start_hour = gym_class["hour"].split(" - ")[0]
                hour, minute = map(int, start_hour.split(":"))
            except Exception:
                # Si el formato de hora está mal, ignoramos esa gym_class
                continue

            # ➕ Agregar minuto adicional si está activado
            activation_hour, activation_minute = should_add_a_minute_for_x(
                config.get("ADDITIONAL_MINUTE_FOR_EXECUTION"), hour, minute
            )

            # 🎯 Comparación exacta
            if now.hour == activation_hour and now.minute == activation_minute:
                gym_classes.append({**gym_class, "day": day_name})

    return gym_classes


def get_classes():
    return is_force_run() if config.get("BOT_FORCE_RUN") else is_regular_run()
