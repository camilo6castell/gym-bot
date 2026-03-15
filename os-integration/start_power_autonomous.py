import os
import yaml
import pytz
import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEDULE_FILE = BASE_DIR / "config" / "classes.yaml"
WAKEALARM = "/sys/class/rtc/rtc0/wakealarm"

WAKE_BEFORE = int(os.getenv("WAKE_MINUTES_BEFORE", 3))

DAY_MAP = {
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


def load_schedule():
    if not SCHEDULE_FILE.exists():
        return {}
    with open(SCHEDULE_FILE) as f:
        return yaml.safe_load(f) or {}


def get_now(schedule):
    tz = pytz.timezone(schedule.get("timezone", "UTC"))
    return datetime.datetime.now(tz)


def find_next_reservation(schedule):
    now = get_now(schedule)
    upcoming = []

    for day_name, classes in schedule.get("dias", {}).items():
        if day_name.lower() not in DAY_MAP:
            continue

        class_weekday = DAY_MAP[day_name.lower()]
        reservation_weekday = (class_weekday + 2) % 7

        for c in classes:
            try:
                start_hour = c["hora"].split(" - ")[0]
                hour, minute = map(int, start_hour.split(":"))
            except Exception:
                continue

            days_ahead = (reservation_weekday - now.weekday()) % 7

            reservation_date = now + datetime.timedelta(days=days_ahead)
            reservation_date = reservation_date.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0
            )

            if reservation_date <= now:
                reservation_date += datetime.timedelta(days=7)

            upcoming.append(reservation_date)

    return min(upcoming) if upcoming else None


def set_wake_alarm(dt):
    timestamp = int(dt.timestamp())
    with open(WAKEALARM, "w") as f:
        f.write("0")
    with open(WAKEALARM, "w") as f:
        f.write(str(timestamp))


def suspend():
    import subprocess
    subprocess.run(["sudo","systemctl", "suspend"], check=True)


def main():
    schedule = load_schedule()
    if not schedule or "dias" not in schedule:
        print("No schedule configured.")
        return

    next_reservation = find_next_reservation(schedule)
    if not next_reservation:
        print("No upcoming reservations.")
        return

    wake_time = next_reservation - datetime.timedelta(minutes=WAKE_BEFORE)

    print("Next reservation:", next_reservation)
    print("Scheduling wake at:", wake_time)

    set_wake_alarm(wake_time)
    print("Suspending...")
    suspend()


if __name__ == "__main__":
    main()