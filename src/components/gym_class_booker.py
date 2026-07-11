"""Búsqueda y reserva de una clase específica dentro del horario del día."""

from __future__ import annotations

from playwright.sync_api import Page

from src.components.gym_class_acceptance import ClassAcceptance
from src.components.gym_class_checker import ClassChecker
from src.utils.human_behavior import human_delay
from src.utils.logger import logger
from src.utils.page_utils import wait_network_idle
from src.utils.recovery import Recovery
from src.utils.strings import str_normalizer


class ClassBooker:
    """
    Localiza el botón de una clase específica dentro del horario del día
    seleccionado, la reserva y verifica que quedó registrada.
    """

    def __init__(
        self,
        acceptance: ClassAcceptance,
        checker: ClassChecker,
        recovery: Recovery,
    ) -> None:
        self._acceptance = acceptance
        self._checker = checker
        self._recovery = recovery

    def book(self, page: Page, gym_class_name: str, gym_class_hour: str) -> None:
        """Busca la clase por nombre y hora, la reserva y verifica la reserva."""
        logger.info(f"🔎 → Buscando clase '{gym_class_name}' en horario '{gym_class_hour}'")

        wait_network_idle(page)
        self._recovery.with_soft_recovery(
            lambda: page.wait_for_selector("#contenedor-horarios", timeout=10000),
            page,
            "Esperando contenedor de horarios",
        )

        botones = page.query_selector_all("button.btn-theme-inverse:not([disabled])")

        for boton in botones:
            texto = str_normalizer(boton.inner_text())
            if str_normalizer(gym_class_name) in texto and gym_class_hour in texto:
                human_delay()
                boton.click()
                logger.success("✔️ → Clase seleccionada correctamente")
                self._recovery.with_soft_recovery(
                    lambda: self._acceptance.confirm(page),
                    page,
                    "Confirmando reserva en sistema",
                )
                self._recovery.with_soft_recovery(
                    lambda: self._checker.verify(page, gym_class_name, gym_class_hour),
                    page,
                    f"Verificando '{gym_class_name}' a las '{gym_class_hour}'",
                )
                return

        logger.warning("⛔ → Clase objetivo no encontrada o no disponible")
