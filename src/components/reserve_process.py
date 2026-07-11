"""Orquestación del flujo completo de reserva de una clase."""

from __future__ import annotations

from playwright.sync_api import Page

from src.components.day_selector import DateSelector
from src.components.gym_class_booker import ClassBooker
from src.components.membership import MembershipSelector
from src.types.config import EnvironmentConfig, ExecutionConfig
from src.utils.logger import logger
from src.utils.page_utils import confirm_url


class ReservationProcess:
    """
    Orquesta el flujo de reserva de una clase: confirma la URL del sistema,
    selecciona el método de acceso, elige la fecha y reserva la clase.

    No implementa lógica propia de UI — delega en `MembershipSelector`,
    `DateSelector` y `ClassBooker`, cada una responsable de un paso.
    """

    def __init__(
        self,
        env_config: EnvironmentConfig,
        execution_config: ExecutionConfig,
        date_selector: DateSelector,
        membership_selector: MembershipSelector,
        class_booker: ClassBooker,
    ) -> None:
        self._env = env_config
        self._execution = execution_config
        self._date_selector = date_selector
        self._membership_selector = membership_selector
        self._class_booker = class_booker

    def reserve(
        self,
        page: Page,
        spanish_day_name: str,
        gym_class_name: str,
        gym_class_hour: str,
    ) -> None:
        """Ejecuta el flujo completo: acceso → selección de fecha → reserva."""
        confirm_url(page, self._env.inside_system_url)

        self._membership_selector.use_membership(page)

        day_selected = (
            self._date_selector.select_by_day(page, spanish_day_name)
            if self._execution.bot_force_run
            else self._date_selector.select_latest_date(page)
        )

        if not day_selected:
            logger.warning(f"⚠️ → Día '{spanish_day_name}' no encontrado, saltando.")
            return

        self._class_booker.book(page, gym_class_name, gym_class_hour)
