from pathlib import Path
from datetime import datetime
import pytz
from src.config.config import Config
from src.utils.logger import logger
from src.utils.time_utils import days_mapper

_config = Config(env_file=str(Path(__file__).resolve().parent.parent / ".env"))
_schedule = _config.get("SCHEDULE")
_execution = _config.get("APP_CONFIG").get("execution", {})
_tz = pytz.timezone(_schedule.get("timezone", "UTC"))


def get_classes() -> list[dict[str, str]]:
    return _is_force_run() if _execution.get("bot_force_run") else _is_regular_run()


def _is_force_run() -> list[dict[str, str]]:
    logger.warning("⚠️ → BOT_FORCE_RUN activo ⚠️")
    forced = _schedule.get("forcedClass")

    if not forced or not all(
        [forced.get("name"), forced.get("hour"), forced.get("day")]
    ):
        raise ValueError(
            "❌ → BOT_FORCE_RUN activo pero faltan datos en 'forcedClass' del schedule."
        )

    return [forced]


def _is_regular_run() -> list[dict[str, str]]:
    if not _schedule or "days" not in _schedule:
        return []

    # ← now se calcula aquí, fresco en cada llamada
    now = datetime.now(_tz)
    target_weekday = (now.weekday() - 2) % 7
    gym_classes: list[dict[str, str]] = []

    for day_name, day_classes in _schedule.get("days", {}).items():
        if days_mapper(day_name) != target_weekday:
            continue
        if not day_classes:
            continue

        for gym_class in day_classes:
            try:
                start_hour = gym_class["hour"].split(" - ")[0]
                hour, minute = map(int, start_hour.split(":"))
            except Exception:
                continue

            activation_hour, activation_minute = _apply_execution_adjustment(
                hour, minute
            )

            if now.hour == activation_hour and now.minute == activation_minute:
                gym_classes.append({**gym_class, "day": day_name})

    return gym_classes


def _apply_execution_adjustment(hour: int, minute: int) -> tuple[int, int]:
    adjustment = _execution.get("execution_adjustment", 0)
    if adjustment == 0:
        return hour, minute

    minute += adjustment
    if minute < 0:
        hour -= 1
        minute += 60
    elif minute >= 60:
        hour += 1
        minute -= 60

    hour = hour % 24
    return hour, minute
