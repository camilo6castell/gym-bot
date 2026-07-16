"""Flujo de navegación posterior al inicio de sesión."""

from __future__ import annotations

from playwright.sync_api import Page

from src.types.config import EnvironmentConfig, SelectorsConfig
from src.utils.logger import logger
from src.utils.page_utils import (
    monitor_new_page,
    search_and_click,
    wait_for_redirect,
    wait_network_idle,
)
from src.utils.recovery import Recovery


class PostLoginPage:
    """Navega desde la pantalla post-login hasta la sección de reservas."""

    def __init__(
        self,
        env_config: EnvironmentConfig,
        selectors_config: SelectorsConfig,
        recovery: Recovery,
    ) -> None:
        self._env = env_config
        self._selectors = selectors_config
        self._recovery = recovery

    def perform_post_login(self, page: Page) -> None:
        """Ejecuta el flujo de navegación después del inicio de sesión."""
        # Espera a que la red esté inactiva después del login
        wait_network_idle(page)

        logger.info("🚀 → Iniciando flujo post-login")

        # Navega a la sección de entrenamiento usando el selector de enlace
        search_and_click(page, "a[href='#mm-m1-p2']", timeout=10000)

        # Accede a la página de práctica libre
        search_and_click(page, "a[href='/sistema.php/entrenamiento/reserva/practica/libre']")

        # Monitorea nuevas páginas que puedan aparecer durante la navegación
        monitor_new_page(
            page, self._recovery, self._selectors.potential_intermediate_login_selector
        )

        # Espera a que ocurra un redireccionamiento a la URL del sistema
        wait_for_redirect(page, self._env.inside_system_url_pattern)

        logger.info("✅ → Flujo post-login completado, dentro del sistema.")
