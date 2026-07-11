import datetime
import subprocess
from zoneinfo import ZoneInfo

from src.settings.provider import Settings
from src.utils.logger import logger
from src.utils.time_utils import days_mapper

_config = Settings()
_power = _config.get("APP_CONFIG").get("power_autonomous", {})
_tz = ZoneInfo(_config.get("SCHEDULE").get("timezone", "UTC"))


def get_now() -> datetime.datetime:
    return datetime.datetime.now(_tz)


def find_next_reservation() -> datetime.datetime | None:
    now = get_now()
    upcoming: list[datetime.datetime] = []

    for day_name, gym_classes in _config.get("SCHEDULE").get("days", {}).items():
        reservation_weekday = (days_mapper(day_name) + 2) % 7

        for gym_class in gym_classes:
            try:
                start_hour = gym_class["hour"].split(" - ")[0]
                hour, minute = map(int, start_hour.split(":"))
            except Exception:
                continue

            days_ahead = (reservation_weekday - now.weekday()) % 7
            reservation_date = (now + datetime.timedelta(days=days_ahead)).replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )

            if reservation_date <= now:
                reservation_date += datetime.timedelta(days=7)

            upcoming.append(reservation_date)

    return min(upcoming) if upcoming else None


def set_wake_alarm(dt: datetime.datetime) -> None:
    wakealarm_path = _power.get("wakealarm_path")
    timestamp = int(dt.timestamp())
    with open(wakealarm_path, "w") as f:
        f.write("0")
    with open(wakealarm_path, "w") as f:
        f.write(str(timestamp))


def suspend() -> None:
    """Suspender el sistema con manejo de errores"""
    try:
        subprocess.run(["/usr/bin/sudo", "-n", "/usr/bin/systemctl", "suspend"], check=True)
    except Exception as e:
        logger.error(f"❌ Error al suspender: {str(e)}", exc_info=True)
        raise
