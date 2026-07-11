"""Flujo de inicio de sesión en la plataforma."""

from __future__ import annotations

from playwright.sync_api import Page

from src.types.config import EnvironmentConfig, SelectorsConfig
from src.utils.human_behavior import human_click, human_delay, human_type
from src.utils.logger import logger
from src.utils.page_utils import dismiss_if_present, monitor_new_page, raise_if_captcha
from src.utils.recovery import Recovery


class LoginPage:
    """
    Encapsula el proceso de inicio de sesión: selección de tipo de
    documento, ingreso de credenciales y envío del formulario.
    """

    def __init__(
        self,
        env_config: EnvironmentConfig,
        selectors_config: SelectorsConfig,
        recovery: Recovery,
        doc_type: str,
        doc_num: str,
        password: str,
    ) -> None:
        """
        Parameters
        ----------
        env_config : EnvironmentConfig
            URLs de la plataforma (login, sistema interno, etc.).
        selectors_config : SelectorsConfig
            Selectores CSS de elementos de UI potencialmente presentes.
        recovery : Recovery
            Usado para manejar modales inesperados tras el envío del formulario.
        doc_type, doc_num, password : str
            Credenciales de acceso a la plataforma.
        """
        self._env = env_config
        self._selectors = selectors_config
        self._recovery = recovery
        self._doc_type = doc_type
        self._doc_num = doc_num
        self._password = password

    def perform_login(self, page: Page) -> None:
        """Realiza el proceso de inicio de sesión en la aplicación."""
        logger.info("🌐 → Abriendo página de login")
        page.goto(self._env.login_url, wait_until="domcontentloaded")
        raise_if_captcha(page)  # Verifica y maneja cualquier CAPTCHA presente

        # Descarta notificaciones temporales si están presentes
        if self._selectors.potential_temporary_platform_notification:
            dismiss_if_present(
                page,
                self._selectors.potential_temporary_platform_notification,
                timeout=5000,
            )

        logger.info("🫆 → Seleccionando tipo de documento")
        page.wait_for_selector("#tipodoc", timeout=20000)
        human_click(page, "#tipodoc")
        human_delay()
        page.select_option("#tipodoc", value=self._doc_type)
        human_delay()

        page.wait_for_selector("#numdoc:not([disabled])", timeout=10000)
        logger.info("🫆 → Ingresando número de documento")
        human_type(page, "#numdoc", self._doc_num)
        human_delay()

        logger.info("🫆 → Ingresando contraseña")
        human_type(page, "#clavepwd", self._password)
        human_delay()
        raise_if_captcha(page)  # Verifica nuevamente por CAPTCHA después de ingresar la contraseña

        page.mouse.wheel(0, 200)  # Scroll para simular comportamiento humano
        human_delay()

        logger.info("🕒 → Enviando formulario")
        page.wait_for_selector("button[type='submit']:not([disabled])", timeout=5000)
        human_click(page, "button[type='submit']")

        # Monitorea nuevas páginas después del envío
        monitor_new_page(page, self._recovery, self._selectors.potential_modal_entiendo_selector)
