import sys
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import Config
from os_integration.os_integration_utils import (
    find_next_reservation,
    set_wake_alarm,
    suspend,
)

config = Config(env_file=".env")


def main():
    next_reservation = find_next_reservation()
    if not next_reservation:
        print("No upcoming reservations.")
        return

    wake_time = next_reservation - datetime.timedelta(
        minutes=config.get("WAKE_MINUTES_BEFORE")
    )

    print("Next reservation:", next_reservation)
    print("Scheduling wake at:", wake_time)

    set_wake_alarm(wake_time)
    print("Suspending...")
    suspend()


if __name__ == "__main__":
    main()
