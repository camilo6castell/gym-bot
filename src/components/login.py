from playwright.sync_api import Page

from src.settings.provider import Settings
from src.utils.human_behavior import human_click, human_delay, human_type
from src.utils.logger import logger
from src.utils.page_utils import dismiss_if_present, monitor_new_page, raise_if_captcha

_config = Settings()
_env = _config.get("APP_CONFIG").get("environment", {})
_selectors = _config.get("APP_CONFIG").get("selectors", {})


def perform_login(page: Page) -> None:
    """
    Realiza el proceso de inicio de sesión en la aplicación.

    Args:
        page (Page): Objeto de la página de Playwright
    """
    logger.info("🌐 → Abriendo página de login")
    page.goto(_env.get("login_url"), wait_until="domcontentloaded")
    raise_if_captcha(page)  # Verifica y maneja cualquier CAPTCHA presente

    # Descarta notificaciones temporales si están presentes
    dismiss_if_present(
        page, _selectors.get("potential_temporary_platform_notification"), timeout=5000
    )

    logger.info("🫆 → Seleccionando tipo de documento")
    page.wait_for_selector(
        "#tipodoc", timeout=20000
    )  # Espera a que el selector de tipo de documento esté disponible
    human_click(page, "#tipodoc")  # Simula clic en el campo de tipo de documento
    human_delay()
    page.select_option(
        "#tipodoc", value=_config.get("COMPENSAR_DOC_TYPE")
    )  # Selecciona el tipo de documento configurado
    human_delay()

    page.wait_for_selector(
        "#numdoc:not([disabled])", timeout=10000
    )  # Espera a que el campo de número de documento esté habilitado
    logger.info("🫆 → Ingresando número de documento")
    human_type(
        page, "#numdoc", _config.get("COMPENSAR_DOC_NUM")
    )  # Ingresa el número de documento configurado
    human_delay()

    logger.info("🫆 → Ingresando contraseña")
    human_type(
        page, "#clavepwd", _config.get("COMPENSAR_PASSWORD")
    )  # Ingresa la contraseña configurada
    human_delay()
    raise_if_captcha(page)  # Verifica nuevamente por CAPTCHA después de ingresar la contraseña

    page.mouse.wheel(0, 200)  # Scroll para simular comportamiento humano
    human_delay()

    logger.info("🕒 → Enviando formulario")
    page.wait_for_selector(
        "button[type='submit']:not([disabled])", timeout=5000
    )  # Espera a que el botón de envío esté disponible
    human_click(page, "button[type='submit']")  # Simula clic en el botón de envío

    # Monitorea nuevas páginas después del envío
    monitor_new_page(page, _selectors.get("potential_modal_entiendo_selector"))
