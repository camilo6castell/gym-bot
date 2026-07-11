"""Selección de fecha disponible para la reserva de una clase."""

from __future__ import annotations

from playwright.sync_api import ElementHandle, Page

from src.utils.human_behavior import human_delay
from src.utils.logger import logger
from src.utils.page_utils import wait_network_idle
from src.utils.recovery import Recovery
from src.utils.strings import str_normalizer


class DateSelector:
    """Selecciona la fecha de reserva, ya sea la más próxima o una específica."""

    def __init__(self, recovery: Recovery) -> None:
        self._recovery = recovery

    def select_latest_date(self, page: Page) -> bool:
        """Selecciona la última fecha disponible en el selector de fechas."""
        logger.info("🏃 → Seleccionando última fecha disponible...")
        last_button = self._get_available_date_buttons(page)[-1]
        human_delay()
        last_button.click()
        logger.success("✔️ → Última fecha seleccionada")
        return True

    def select_by_day(self, page: Page, spanish_day_name: str) -> bool:
        """Busca y selecciona la fecha que corresponde al día indicado (en español)."""
        logger.info(f"🔎 → Buscando fecha correspondiente a '{spanish_day_name}'")

        for button in self._get_available_date_buttons(page):
            text = str_normalizer(button.inner_text())
            if spanish_day_name in text:
                human_delay()
                button.click()
                logger.success(f"🕒 → Fecha seleccionada: {text}")
                return True

        logger.warning(f"⛔ → No se encontró el día '{spanish_day_name}'")
        return False

    def _get_available_date_buttons(self, page: Page) -> list[ElementHandle]:
        wait_network_idle(page)
        self._recovery.with_soft_recovery(
            lambda: page.wait_for_selector("button.botonfecha", timeout=10000),
            page,
            "Esperando botones de fecha disponibles",
        )
        return page.query_selector_all("button.botonfecha")
