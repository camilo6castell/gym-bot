import sys
import time
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import Config
from os_integration.os_integration_utils import (
    get_now,
    find_next_reservation,
    set_wake_alarm,
    suspend,
)

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
config = Config(env_file=str(ENV_FILE))


def main():
    next_reservation = find_next_reservation()
    if not next_reservation:
        print("No upcoming reservations")
        return

    wake_time = next_reservation - datetime.timedelta(
        minutes=config.get("WAKE_MINUTES_BEFORE")
    )
    sleep_time = next_reservation + datetime.timedelta(
        minutes=config.get("SLEEP_MINUTES_AFTER")
    )
    now = get_now()

    print("Now:", now)
    print("Wake at:", wake_time)
    print("Sleep after:", sleep_time)

    # SOLO actuamos si estamos dentro de ventana
    if wake_time <= now <= sleep_time:
        remaining = (sleep_time - now).total_seconds()
        print("Inside active window. Staying awake for", remaining, "seconds")

        time.sleep(max(0, remaining))

        print("Window finished. Scheduling next cycle.")

        next_reservation = find_next_reservation()
        if not next_reservation:
            print("No upcoming reservations after sleep")
            return

        next_wake = next_reservation - datetime.timedelta(
            minutes=config.get("WAKE_MINUTES_BEFORE")
        )

        set_wake_alarm(next_wake)
        print("Suspending for next reservation at:", next_wake)
        suspend()
        return

    print("Outside active window. No suspension triggered.")


if __name__ == "__main__":
    main()
