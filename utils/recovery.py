import time
from typing import Callable, Any
from playwright.sync_api import Page
from notifications.telegram import notify, getUpdates
from utils.logger import logger
from core.env import TOKEN, CHAT_ID


def with_soft_recovery(
    action_fn: Callable,
    page: Page,
    action_name: str = "please specify an action name",
    ms_to_retry: int = 5000,
    max_retries: int = 3,
) -> Any:
    attempts = 0
    last_exception = None

    while attempts <= max_retries:
        try:
            action_fn()
            return  # ✅ éxito — sale de la función, programa continúa
        except Exception as e:
            last_exception = e
            attempts += 1
            remaining = max_retries - attempts
            logger.error(
                f"❌ '{action_name}' falló. "
                f"Intentos restantes: {remaining}. Razón: {e}"
            )
            if attempts > max_retries:
                break
            logger.info(f"⏳ Reintentando en {ms_to_retry}ms...")
            page.wait_for_timeout(ms_to_retry)

    raise RuntimeError(
        f"'{action_name}' falló tras {max_retries} intentos. "
        f"Último error: {last_exception}"
    )


def with_recovery(
    action_fn: Callable,
    page: Page,
    action_name: str = "acción",
    max_retries: int | None = None,
) -> Any:
    """
    Ejecuta action_fn con recuperación ante fallos vía Telegram.

    action_fn: función sin argumentos (usa closure o lambda desde el caller)
    page: necesaria para el refresh
    action_name: nombre descriptivo para los logs y notificaciones
    max_retries: None = infinito hasta timeout o abort
    """
    retry_count = 0

    while True:
        try:
            result = action_fn()
            return result  # éxito
        except Exception as e:
            logger.error(f"❌ Error en '{action_name}': {e}")

            if max_retries is not None and retry_count >= max_retries:
                raise RuntimeError(
                    f"'{action_name}' falló tras {retry_count} intentos."
                )

            action = wait_for_user_action(
                f"Error en: {action_name}\n" f" falló: {e}\n",
                timeout=600,
                retry_count=retry_count,
            )

            if action == "resume":
                retry_count += 1
                continue  # ← solo reintenta, no toca la página
            elif action == "refresh":
                retry_count += 1
                page.reload()
                page.wait_for_load_state("networkidle")
                continue
            elif action == "abort":
                raise RuntimeError(f"Bot abortado durante '{action_name}'.")


def wait_for_user_action(error_description, timeout=600, retry_count=0) -> str:
    full_msg = (
        f"❌{error_description}."
        "\n"
        "\n"
        "\tResponde"
        "\n"
        "0️⃣\tResume\n"
        "1️⃣\tRefresh & Retry"
        "\n"
        "\n"
        f"Intento #{retry_count}."
    )
    notify(full_msg)

    last_update_id = _get_last_update_id()  # ← ver abajo
    start = time.time()

    while time.time() - start < timeout:
        updates = getUpdates()
        for update in updates.get("result", []):
            update_id = update["update_id"]
            if update_id <= last_update_id:
                continue
            last_update_id = update_id

            text = update.get("message", {}).get("text", "").strip()
            if text == "0":
                notify("▶️ Resuming...")
                return "resume"
            if text == "1":
                notify("🔄 Refreshing and retrying...")
                return "refresh"

        time.sleep(5)

    notify("❌ Timeout alcanzado. El bot se detendrá.")
    return "abort"


def _get_last_update_id() -> int:
    """Obtiene el update_id más reciente para ignorar mensajes viejos."""
    updates = getUpdates()
    results = updates.get("result", [])
    return results[-1]["update_id"] if results else 0
