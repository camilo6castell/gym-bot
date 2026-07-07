# src/utils/recovery.py
import time
from typing import Callable, Any, Optional
from playwright.sync_api import Page
from src.notifications.telegram import notify, getUpdates
from src.utils.logger import logger
from src.utils.exceptions import CaptchaDetectedError


class Recovery:
    def __init__(
        self,
    ) -> None:
        """
        Inicializa la clase Recovery con una lista de clases para batch processing.
        """
        self.batch_classes: Optional[list[dict[str, str]]] = None

    def set_batch_classes(self, batch_classes: list[dict[str, str]]) -> None:
        """
        Establece la lista de clases para batch processing.
        """
        self.batch_classes = batch_classes

    def with_soft_recovery(
        self,
        action_fn: Callable[[], Any],
        page: Page,
        action_name: str = "please specify an action name",
        ms_to_retry: int = 5000,
        max_retries: int = 3,
    ) -> None:
        """
        Ejecuta una acción con recuperación suave: reintento automático en caso de error.
        """
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
            f"❌ → '{action_name}' falló tras {max_retries} intentos. "
            f"Último error: {last_exception}"
        )

    def with_recovery(
        self,
        action_fn: Callable[[], Any],
        page: Page,
        action_name: str = "acción",
        max_retries: Optional[int] = 3,
        auto_refresh_limit: int = 2,
    ) -> None:
        """
        Ejecuta una acción con recuperación avanzada: reintento automático y manejo de CAPTCHA.
        """
        retry_count = 0
        auto_refreshes = 0

        while True:
            try:
                action_fn()
                return

            except CaptchaDetectedError:
                logger.warning(f"🔒 → CAPTCHA en '{action_name}', solicitando ayuda...")
                action = self.wait_for_user_action(
                    f"🔒 → CAPTCHA detectado en: {action_name}\nResuélvelo y responde.",
                    timeout=600,
                    retry_count=retry_count,
                )
                retry_count, auto_refreshes = self._handle_user_action(
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

                action = self.wait_for_user_action(
                    f"❌ → Error en: {action_name}\nfalló: {e}\n(después de {auto_refresh_limit} auto-refreshes)",
                    timeout=600,
                    retry_count=retry_count,
                )
                retry_count, auto_refreshes = self._handle_user_action(
                    action, page, action_name, retry_count, auto_refreshes
                )

    def wait_for_user_action(
        self,
        error_description: str,
        timeout: int = 600,
        retry_count: int = 0,
    ) -> str:
        """
        Espera una acción del usuario a través de Telegram.
        """
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

        last_update_id = self._get_last_update_id()  # ← ver abajo
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
        self,
        action: str,
        page: Page,
        action_name: str,
        retry_count: int,
        auto_refreshes: int,
    ) -> tuple[int, int]:
        """
        Ejecuta la acción del usuario y retorna (retry_count, auto_refreshes) actualizados.
        """
        if action == "resume":
            return retry_count + 1, 0
        elif action == "refresh":
            page.reload()
            page.wait_for_load_state("networkidle")
            return retry_count + 1, 0
        elif action == "abort":
            raise RuntimeError(f"❌ → Bot abortado durante '{action_name}'.")
        return retry_count, auto_refreshes

    def _get_last_update_id(self) -> int:
        """
        Obtiene el update_id más reciente para ignorar mensajes viejos.
        """
        updates = getUpdates()
        results = updates.get("result", [])
        return results[-1]["update_id"] if results else 0

recovery: Recovery = Recovery()