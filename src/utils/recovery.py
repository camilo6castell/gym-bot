import time
from typing import Callable, Any
from playwright.sync_api import Page
from notifications.telegram import notify, getUpdates
from utils.logger import logger
from utils.exceptions import CaptchaDetectedError


def with_soft_recovery(
    action_fn: Callable[[], Any],
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
                f"❌ → '{action_name}' falló. "
                f"Intentos restantes: {remaining}. Razón: {e}"
            )
            if attempts > max_retries:
                break
            logger.info(f"⏳ → Reintentando en {ms_to_retry}ms...")
            page.wait_for_timeout(ms_to_retry)

    raise RuntimeError(
        f"❌ → ''{action_name}' falló tras {max_retries} intentos. "
        f"Último error: {last_exception}"
    )


def with_recovery(
    action_fn: Callable[[], Any],
    page: Page,
    action_name: str = "acción",
    max_retries: int | None = 3,
    auto_refresh_limit: int = 2,
) -> Any:
    retry_count = 0
    auto_refreshes = 0

    while True:
        try:
            return action_fn()

        except CaptchaDetectedError:
            logger.warning(f"🔒 → CAPTCHA en '{action_name}', solicitando ayuda...")
            action = wait_for_user_action(
                f"🔒 → CAPTCHA detectado en: {action_name}\nResuélvelo y responde.",
                timeout=600,
                retry_count=retry_count,
            )
            retry_count, auto_refreshes = _handle_user_action(
                action, page, action_name, retry_count, auto_refreshes
            )

        except Exception as e:
            logger.error(f"❌ → Error en '{action_name}': {e}")

            if max_retries is not None and retry_count >= max_retries:
                raise RuntimeError(
                    f"❌ → '{action_name}' falló tras {retry_count} intentos."
                )

            if auto_refreshes < auto_refresh_limit:
                auto_refreshes += 1
                retry_count += 1
                logger.info(
                    f"🔄 → Auto-refresh {auto_refreshes}/{auto_refresh_limit} para '{action_name}'..."
                )
                page.reload()
                page.wait_for_load_state("networkidle")
                continue

            action = wait_for_user_action(
                f"❌ → Error en: {action_name}\nfalló: {e}\n(después de {auto_refresh_limit} auto-refreshes)",
                timeout=600,
                retry_count=retry_count,
            )
            retry_count, auto_refreshes = _handle_user_action(
                action, page, action_name, retry_count, auto_refreshes
            )


def wait_for_user_action(
    error_description: str, timeout: int = 600, retry_count: int = 0
) -> str:
    full_msg = (
        f"❌ → {error_description}."
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
                notify("▶️ → Resuming...")
                return "resume"
            if text == "1":
                notify("🔄 → Refreshing and retrying...")
                return "refresh"

        time.sleep(5)

    notify("❌ → Timeout de recovery alcanzado. El bot se detendrá.")
    return "abort"


def _handle_user_action(
    action: str, page: Page, action_name: str, retry_count: int, auto_refreshes: int
) -> tuple[int, int]:
    """Ejecuta la acción del usuario y retorna (retry_count, auto_refreshes) actualizados."""
    if action == "resume":
        return retry_count + 1, 0
    elif action == "refresh":
        page.reload()
        page.wait_for_load_state("networkidle")
        return retry_count + 1, 0
    elif action == "abort":
        raise RuntimeError(f"❌ → Bot abortado durante '{action_name}'.")
    return retry_count, auto_refreshes


def _get_last_update_id() -> int:
    """Obtiene el update_id más reciente para ignorar mensajes viejos."""
    updates = getUpdates()
    results = updates.get("result", [])
    return results[-1]["update_id"] if results else 0
