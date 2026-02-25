import os
from playwright.sync_api import Page, TimeoutError
from loguru import logger

from bot.browser import human_delay
from bot.fecha_y_clase import seleccionar_ultima_fecha, seleccionar_clase
from bot.confirmacion import confirmar_reserva


# ---------------------------------------------------
# UTILIDADES
# ---------------------------------------------------


def wait_network_idle(page: Page, timeout=15000):
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except:
        pass


def click_if_exists(page: Page, selector: str, timeout=5000):
    try:
        page.wait_for_selector(selector, timeout=timeout)
        page.click(selector)
        return True
    except TimeoutError:
        return False


def wait_if_captcha(page: Page):
    try:
        page.wait_for_selector("iframe[src*='captcha']", timeout=4000)
        logger.warning("⚠️ CAPTCHA detectado. Resuélvelo manualmente...")
        page.pause()
    except TimeoutError:
        pass


# ---------------------------------------------------
# AUTENTICACIÓN INTERMEDIA
# ---------------------------------------------------


def handle_presso_login(page: Page):
    if click_if_exists(page, "#presso-login", timeout=8000):
        logger.info("Detectado 'Ingresa con Compensar'")
        wait_network_idle(page)
        page.wait_for_url("**deportescompensar.com/**", timeout=30000)
        logger.success("Autenticación compensar completada")


# ---------------------------------------------------
# ASEGURAR LANDING
# ---------------------------------------------------


def ensure_in_plan_bienestar(page: Page):

    logger.info(f"URL actual: {page.url}")

    if "sistemared" in page.url:
        logger.info("Esperando redirección desde sistemared...")
        try:
            page.wait_for_url("**planbienestar**", timeout=8000)
        except TimeoutError:
            logger.info("Forzando acceso manual...")
            page.goto(
                "https://sistemaplanbienestar.deportescompensar.com/"
                "entrenamiento/reserva/practica/libre",
                wait_until="networkidle",
            )

    handle_presso_login(page)

    page.wait_for_url("**planbienestar**", timeout=20000)
    wait_network_idle(page)
    wait_if_captcha(page)

    logger.success(f"Estamos dentro: {page.url}")


# ---------------------------------------------------
# MEMBRESÍA
# ---------------------------------------------------


def open_plan_and_use_membership(page: Page):

    handle_presso_login(page)

    logger.info("🔎 Buscando botones 'Usar Membresía' o 'Usar tiquetera'...")

    try:
        # Esperar a que aparezca cualquiera de los dos textos
        page.wait_for_selector(
            'button:has-text("Usar Membresía"), button:has-text("Usar tiquetera")',
            timeout=20000
        )

        # Locator que contempla ambas opciones
        buttons = page.locator(
            'button:has-text("Usar Membresía"), button:has-text("Usar tiquetera")'
        )

        count = buttons.count()

        if count == 0:
            raise Exception("No se encontraron botones de membresía ni tiquetera.")

        logger.info(f"🧩 {count} botón(es) encontrados. Evaluando...")

        # Buscar el primer botón visible y habilitado
        for i in range(count):
            btn = buttons.nth(i)

            if btn.is_visible() and btn.is_enabled():
                text = btn.inner_text()
                logger.info(f"✅ Usando botón índice {i} → '{text}'")
                btn.click()
                wait_network_idle(page)
                logger.success("🎟️ Método de acceso seleccionado correctamente")
                return

        raise Exception("Se encontraron botones pero ninguno estaba habilitado.")

    except TimeoutError:
        logger.error("⏰ Timeout esperando botones de membresía/tiquetera")
        raise

    except Exception as e:
        logger.error(f"❌ Error seleccionando método de acceso: {e}")
        raise


# ---------------------------------------------------
# FLUJO PRINCIPAL
# ---------------------------------------------------

force_run = os.getenv("BOT_FORCE_RUN", "false").lower() == "true"
force_day = os.getenv("BOT_FORCE_RUN_DAY")


def run_post_login_flow(page: Page, clase_objetivo: dict):

    ensure_in_plan_bienestar(page)
    open_plan_and_use_membership(page)

    if force_run and force_day:
        from bot.fecha_y_clase import seleccionar_fecha_por_dia

        seleccionar_fecha_por_dia(page, force_day)
    else:
        seleccionar_ultima_fecha(page)

    handle_presso_login(page)

    seleccionar_clase(
        page, nombre_clase=clase_objetivo["nombre"], horario=clase_objetivo["hora"]
    )

    confirmar_reserva(page)

    logger.success("🎉 Reserva completada")

    page.wait_for_timeout(1500)
