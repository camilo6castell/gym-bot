"""Post-login navigation flow."""

from __future__ import annotations

from src.types.browser import IPage
from src.types.config import EnvironmentConfig, SelectorsConfig
from src.utils.logger import logger
from src.utils.page_utils import (
    dismiss_if_present,
    navigate_by_clicks,
    wait_for_redirect,
    wait_network_idle,
)
from src.utils.recovery import Recovery


class PostLoginPage:
    """Navigate from the post-login screen to the reservation section."""

    def __init__(
        self,
        env_config: EnvironmentConfig,
        selectors_config: SelectorsConfig,
        recovery: Recovery,
    ) -> None:
        self._env = env_config
        self._selectors = selectors_config
        self._recovery = recovery

    def perform_post_login(self, page: IPage) -> None:
        """Execute post-login navigation: training section → free practice → reservation."""
        wait_network_idle(page)

        logger.info("🚀 → Starting post-login flow")

        navigate_by_clicks(
            page,
            [
                "#mainMenu",
                "a[href='#mm-m1-p2']",
                "a[href='/sistema.php/entrenamiento/reserva/practica/libre']",
            ],
        )

        wait_network_idle(page)

        if self._selectors.potential_intermediate_login_selector:
            dismiss_if_present(
                page,
                self._selectors.potential_intermediate_login_selector,
                True,
                timeout=10000,
            )

        wait_for_redirect(page, self._env.inside_system_url_pattern)

        logger.info("✅ → Post-login flow complete, inside the system.")
