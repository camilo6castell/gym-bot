"""Verify that a class was successfully booked."""

from __future__ import annotations

from src.types.browser import IPage
from src.utils.exceptions import ReservationVerificationError
from src.utils.human_behavior import human_delay
from src.utils.logger import logger
from src.utils.page_utils import search_and_click, wait_network_idle
from src.utils.recovery import Recovery
from src.utils.strings import str_normalizer
from src.utils.time_utils import military_time_range_to_ampm


class ClassChecker:
    """Verify in the 'Mis turnos' section that a reservation was recorded."""

    def __init__(self, recovery: Recovery) -> None:
        self._recovery = recovery

    def verify(self, page: IPage, gym_class_name: str, gym_class_hour: str) -> None:
        """
        Confirm the reserved class appears in 'Mis turnos'.

        Raises
        ------
        ReservationVerificationError
            If the reservation is not found in the upcoming sessions list.
        """
        logger.info(f"🔍 → Verifying reservation: '{gym_class_name}' | '{gym_class_hour}'")

        wait_network_idle(page, timeout=20000)

        search_and_click(page, "#mainMenu", timeout=10000)
        search_and_click(page, "a[href='#mm-m1-p2']")
        search_and_click(page, "a[href='/sistema.php/entrenamiento/mis/turnos']")

        self._recovery.with_soft_recovery(
            lambda: page.wait_for_selector(
                ".panel-proximos-turno .ng-binding, .panel.panel-shadow .ng-binding",
                timeout=15000,
            ),
            page,
            "Waiting for upcoming sessions content",
        )

        human_delay(1.5, 2.5)

        ampm_hour = military_time_range_to_ampm(gym_class_hour)
        normalized_name = str_normalizer(gym_class_name)
        normalized_hour = str_normalizer(ampm_hour)

        cards = page.query_selector_all(".panel-proximos-turno, .panel.panel-shadow[ng-repeat]")

        logger.info(f"🔍 → Cards found: {len(cards)}")

        for card in cards:
            text = str_normalizer(card.inner_text())
            if normalized_name in text and normalized_hour in text:
                logger.success(f"✅ → Reservation confirmed: '{gym_class_name}' | '{ampm_hour}'")
                return

        raise ReservationVerificationError(
            f"❌ Reservation for '{gym_class_name}' "
            f"at '{ampm_hour}' not found. The class may not have been booked correctly."
        )
