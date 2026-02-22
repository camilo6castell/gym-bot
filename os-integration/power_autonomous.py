import os
import yaml
import time
import pytz
import datetime
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEDULE_FILE = BASE_DIR / "config" / "classes.yaml"
WAKEALARM = "/sys/class/rtc/rtc0/wakealarm"

BOT_FORCE_RUN = os.getenv("BOT_FORCE_RUN", "false").lower() == "true"
WAKE_BEFORE = int(os.getenv("WAKE_MINUTES_BEFORE", 3))
SLEEP_AFTER = int(os.getenv("SLEEP_MINUTES_AFTER", 3))

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


# -------------------------
# Config & Timezone
# -------------------------

def load_schedule():
    if not SCHEDULE_FILE.exists():
        return {}
    with open(SCHEDULE_FILE) as f:
        return yaml.safe_load(f) or {}


def get_now(schedule):
    timezone_str = schedule.get("timezone", "UTC")
    tz = pytz.timezone(timezone_str)
    return datetime.datetime.now(tz)


# -------------------------
# RTC Helpers
# -------------------------

def read_wakealarm():
    try:
        with open(WAKEALARM, "r") as f:
            value = f.read().strip()
            return int(value) if value else None
    except Exception:
        return None


def set_wake_alarm(dt):
    timestamp = int(dt.timestamp())

    with open(WAKEALARM, "w") as f:
        f.write("0")

    with open(WAKEALARM, "w") as f:
        f.write(str(timestamp))


def suspend():
    subprocess.run(["systemctl", "suspend"], check=True)


# -------------------------
# Reservation Calculation
# -------------------------

def find_next_reservation(schedule):
    now = get_now(schedule)
    upcoming_reservations = []

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

            upcoming_reservations.append(reservation_date)

    if not upcoming_reservations:
        return None

    return min(upcoming_reservations)


# -------------------------
# Main Logic (Single Cycle)
# -------------------------

def main():
    if BOT_FORCE_RUN:
        print("BOT_FORCE_RUN=true → Power mode disabled")
        return

    schedule = load_schedule()

    if not schedule or "dias" not in schedule:
        print("No schedule configured")
        return

    next_reservation = find_next_reservation(schedule)

    if not next_reservation:
        print("No upcoming reservations found")
        return

    wake_time = next_reservation - datetime.timedelta(minutes=WAKE_BEFORE)
    sleep_time = next_reservation + datetime.timedelta(minutes=SLEEP_AFTER)
    now = get_now(schedule)

    print("Now:", now)
    print("Next reservation:", next_reservation)
    print("Wake at:", wake_time)
    print("Sleep after:", sleep_time)

    # ------------------------------------------------
    # SOLO actuamos si estamos dentro de ventana
    # ------------------------------------------------
    if wake_time <= now <= sleep_time:
        remaining = (sleep_time - now).total_seconds()
        print("Inside active window. Staying awake for", remaining, "seconds")

        time.sleep(max(0, remaining))

        print("Window finished. Scheduling next cycle.")

        next_reservation = find_next_reservation(schedule)
        next_wake = next_reservation - datetime.timedelta(minutes=WAKE_BEFORE)

        print("Suspending for next reservation at:", next_wake)
        set_wake_alarm(next_wake)
        suspend()
        return

    # ------------------------------------------------
    # FUERA DE VENTANA → NO HACER NADA
    # ------------------------------------------------
    print("Outside active window. No suspension triggered.")
    return


if __name__ == "__main__":
    main()