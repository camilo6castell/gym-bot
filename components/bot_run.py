import pytz
from core.config import Config
from datetime import datetime
from utils.time_utils import days_mapper
from utils.logger import logger
from components.add_a_minute_for_x import should_add_a_minute_for_x

config = Config(env_file=".env")


def is_force_run() -> list[dict[str, str]]:
    logger.warning("⚠️  → BOT_FORCE_RUN activo ⚠️")

    if (
        not config.get("BOT_FORCE_RUN_CLASS")
        or not config.get("BOT_FORCE_RUN_HOUR")
        or not config.get("BOT_FORCE_RUN_DAY")
    ):
        raise ValueError(
            "❌ → Error BOT_FORCE_RUN activo pero faltan datos de clase forzada."
        )

    return [
        {
            "name": config.get("BOT_FORCE_RUN_CLASS"),
            "hour": config.get("BOT_FORCE_RUN_HOUR"),
            "day": config.get("BOT_FORCE_RUN_DAY"),
        }
    ]


def is_regular_run() -> list[dict[str, str]]:
    if not config.get("SCHEDULE") or "days" not in config.get("SCHEDULE"):
        return []

    # 🕒 Zona horaria segura
    timezone_str = config.get("SCHEDULE").get("timezone", "UTC")
    tz = pytz.timezone(timezone_str)
    now = datetime.now(tz)

    # 🔥 Siempre 2 días atrás
    target_weekday = (now.weekday() - 2) % 7

    gym_classes: list[dict[str, str]] = []

    for day_name, day_classes in config.get("SCHEDULE").get("days", {}).items():

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
    print(config.get("BOT_FORCE_RUN"))
    return is_force_run() if config.get("BOT_FORCE_RUN") else is_regular_run()
