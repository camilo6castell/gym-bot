import sys
import pytz
import datetime
import subprocess
import datetime as dt_module
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.time_utils import days_mapper
from core.config import Config

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
config = Config(env_file=str(ENV_FILE))


def get_now():
    tz = pytz.timezone(config.get("SCHEDULE").get("timezone", "UTC"))
    return datetime.datetime.now(tz)


def find_next_reservation() -> Optional[datetime.datetime]:
    now = get_now()
    upcoming: list[datetime.datetime] = []

    for day_name, gym_classes in config.get("SCHEDULE").get("days", {}).items():

        reservation_weekday = (days_mapper(day_name) + 2) % 7

        for gym_class in gym_classes:
            try:
                start_hour = gym_class["hour"].split(" - ")[0]
                hour, minute = map(int, start_hour.split(":"))
            except Exception:
                continue

            days_ahead = (reservation_weekday - now.weekday()) % 7

            reservation_date = now + datetime.timedelta(days=days_ahead)
            reservation_date = reservation_date.replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )

            if reservation_date <= now:
                reservation_date += datetime.timedelta(days=7)

            upcoming.append(reservation_date)

    return min(upcoming) if upcoming else None


def set_wake_alarm(dt: dt_module.datetime) -> None:
    timestamp = int(dt.timestamp())
    wakealarm_path: str = config.get("WAKEALARM_PATH")
    with open(wakealarm_path, "w") as f:
        f.write("0")
    with open(wakealarm_path, "w") as f:
        f.write(str(timestamp))


def suspend():
    subprocess.run(["/usr/bin/sudo", "-n", "/usr/bin/systemctl", "suspend"], check=True)
