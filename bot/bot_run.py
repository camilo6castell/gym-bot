import pytz
from core.config import Config
from datetime import datetime
from utils.time_utils import days_mapper
from utils.logger import logger

config = Config(env_file=".env")
schedule = config.get("SCHEDULE")
# 🕒 Zona horaria segura
timezone_str = schedule.get("timezone")
tz = pytz.timezone(timezone_str)
now = datetime.now(tz)


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
            activation_hour, activation_minute = _execution_adjustment(hour, minute)

            # 🎯 Comparación exacta
            if now.hour == activation_hour and now.minute == activation_minute:
                gym_classes.append({**gym_class, "day": day_name})

    return gym_classes


def get_classes():
    logger.info(f"🏳️  → Inicio: {now.strftime('%H:%M:%S')}")
    return is_force_run() if config.get("BOT_FORCE_RUN") else is_regular_run()


def _execution_adjustment(hour: int, minute: int) -> tuple[int, int]:
    execution_adjustment = config.get("EXECUTION_ADJUSTMENT")
    if execution_adjustment != 0:
        logger.warning("⚠️  → ¡Ajustando tiempo de ejecución! ⚠️")
        minute += execution_adjustment
        if minute < 0:
            hour -= 1
            minute += 60
        if minute >= 60:
            hour += 1
            minute -= 60

        if hour >= 24:
            hour = 0
    return hour, minute
