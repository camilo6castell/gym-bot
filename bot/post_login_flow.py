from playwright.sync_api import Page
from loguru import logger

from bot.browser import human_delay
from bot.fecha_y_clase import seleccionar_ultima_fecha, seleccionar_clase
from bot.confirmacion import confirmar_reserva


def handle_swal_entendido(page: Page):
    try:
        page.wait_for_selector(
            'button.btn.btn-primary:has-text("Entiendo")', timeout=15000
        )
        human_delay()
        page.click('button.btn.btn-primary:has-text("Entiendo")')
    except:
        pass


def wait_for_final_redirect(page: Page):
    page.wait_for_url(
        "https://sistemaplanbienestar.deportescompensar.com/**", timeout=30000
    )


def open_reservas_menu(page: Page):
    page.wait_for_selector(
        'a.mm-subopen.mm-fullsubopen[href="#mm-m1-p2"]', timeout=20000
    )
    human_delay()
    page.click('a.mm-subopen.mm-fullsubopen[href="#mm-m1-p2"]')

    page.wait_for_selector(
        'a[href="/sistema.php/entrenamiento/reserva/practica/libre"]', timeout=15000
    )
    human_delay()
    page.click('a[href="/sistema.php/entrenamiento/reserva/practica/libre"]')


def open_plan_and_use_membership(page: Page):
    page.wait_for_url(
        "**/entrenamiento/reserva/practica/libre#/planes/**", timeout=20000
    )

    page.wait_for_selector(
        'button#botonPlan-0:has-text("Usar Membresía")', timeout=20000
    )
    human_delay()
    page.click("button#botonPlan-0")


def run_post_login_flow(page: Page, clase_objetivo: dict):
    handle_swal_entendido(page)
    wait_for_final_redirect(page)
    open_reservas_menu(page)
    open_plan_and_use_membership(page)

    seleccionar_ultima_fecha(page)

    seleccionar_clase(
        page, nombre_clase=clase_objetivo["nombre"], horario=clase_objetivo["hora"]
    )

    confirmar_reserva(page)

    logger.info("Esperando actualización de la página...")
    page.wait_for_timeout(3000)
