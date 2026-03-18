import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import datetime
from os_integration.os_integration_utils import (
    find_next_reservation,
    set_wake_alarm,
    suspend,
)
from core.env import WAKE_MINUTES_BEFORE


def main():
    next_reservation = find_next_reservation()
    if not next_reservation:
        print("No upcoming reservations.")
        return

    wake_time = next_reservation - datetime.timedelta(minutes=WAKE_MINUTES_BEFORE)

    print("Next reservation:", next_reservation)
    print("Scheduling wake at:", wake_time)

    set_wake_alarm(wake_time)
    print("Suspending...")
    suspend()


if __name__ == "__main__":
    main()
