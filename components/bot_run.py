import pytz
from datetime import datetime
from utils.days_handler import days_mapper
from utils.logger import logger
from core.schedule import load_schedule
from components.add_a_minute_for_x import should_add_a_minute_for_x


def is_force_run(BOT_FORCE_RUN_CLASS, BOT_FORCE_RUN_HOUR, BOT_FORCE_RUN_DAY):
    logger.warning("⚠️ BOT_FORCE_RUN activo ⚠️")

    if not BOT_FORCE_RUN_CLASS or not BOT_FORCE_RUN_HOUR or not BOT_FORCE_RUN_DAY:
        raise ValueError(
            "Error BOT_FORCE_RUN activo pero faltan datos de clase forzada."
        )

    return [
        {
            "name": BOT_FORCE_RUN_CLASS,
            "hour": BOT_FORCE_RUN_HOUR,
            "day": BOT_FORCE_RUN_DAY,
        }
    ]


def is_regular_run(
    ADDITIONAL_MINUTE_FOR_EXECUTION,
):
    schedule = load_schedule()
    if not schedule or "dias" not in schedule:
        return []

    # 🕒 Zona horaria segura
    timezone_str = schedule.get("timezone", "UTC")
    tz = pytz.timezone(timezone_str)
    now = datetime.now(tz)

    # 🔥 Siempre 2 días atrás
    target_weekday = (now.weekday() - 2) % 7

    gym_classes = []

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
                ADDITIONAL_MINUTE_FOR_EXECUTION, hour, minute
            )

            # 🎯 Comparación exacta
            if now.hour == activation_hour and now.minute == activation_minute:
                gym_classes.append({**gym_class, "day": day_name})

    return gym_classes


def get_classes(
    BOT_FORCE_RUN,
    BOT_FORCE_RUN_CLASS,
    BOT_FORCE_RUN_HOUR,
    BOT_FORCE_RUN_DAY,
    ADDITIONAL_MINUTE_FOR_EXECUTION,
):
    return (
        is_force_run(BOT_FORCE_RUN_CLASS, BOT_FORCE_RUN_HOUR, BOT_FORCE_RUN_DAY)
        if BOT_FORCE_RUN
        else is_regular_run(ADDITIONAL_MINUTE_FOR_EXECUTION)
    )
