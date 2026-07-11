"""
Mecanismos de recuperación ante errores durante la automatización.

`Recovery` no crea su propio `TelegramClient`: lo recibe por constructor
(inyección de dependencias), igual que el resto de las clases de la
aplicación. Esto evita estado global oculto y hace que la clase sea
fácil de probar con un notificador falso.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from playwright.sync_api import Page

from src.notifications.telegram import TelegramClient
from src.utils.exceptions import CaptchaDetectedError, RecoveryAbortedError, RecoveryExhaustedError
from src.utils.logger import logger


class Recovery:
    """
    Ejecuta acciones de automatización con distintos niveles de recuperación
    ante fallos: reintento simple (`with_soft_recovery`) y recuperación
    asistida por Telegram con CAPTCHA y auto-refresh (`with_recovery`).
    """

    def __init__(self, notifier: TelegramClient) -> None:
        """
        Parameters
        ----------
        notifier : TelegramClient
            Cliente usado para notificar errores y esperar comandos remotos
            de recuperación (0 = resume, 1 = refresh & retry).
        """
        self._notifier = notifier
        self.batch_classes: list[dict[str, str]] | None = None

    def set_batch_classes(self, batch_classes: list[dict[str, str]]) -> None:
        """Establece la lista de clases del lote actual (para contexto en notificaciones)."""
        self.batch_classes = batch_classes

    def with_soft_recovery(
        self,
        action_fn: Callable[[], Any],
        page: Page,
        action_name: str = "please specify an action name",
        ms_to_retry: int = 5000,
        max_retries: int = 3,
    ) -> None:
        """Ejecuta una acción con recuperación suave: reintento automático en caso de error."""
        attempts = 0
        last_exception: Exception | None = None

        while attempts <= max_retries:
            try:
                action_fn()
                return  # ✅ éxito — sale de la función, programa continúa
            except Exception as e:
                last_exception = e
                attempts += 1
                remaining = max_retries - attempts
                logger.error(
                    f"❌ → '{action_name}' falló. Intentos restantes: {remaining}. Razón: {e}"
                )
                if attempts > max_retries:
                    break
                logger.info(f"⏳ → Reintentando en {ms_to_retry}ms...")
                page.wait_for_timeout(ms_to_retry)

        raise RecoveryExhaustedError(
            f"❌ → '{action_name}' falló tras {max_retries} intentos. "
            f"Último error: {last_exception}"
        )

    def with_recovery(
        self,
        action_fn: Callable[[], Any],
        page: Page,
        action_name: str = "acción",
        max_retries: int | None = 3,
        auto_refresh_limit: int = 2,
    ) -> None:
        """Ejecuta una acción con recuperación avanzada: reintento y manejo de CAPTCHA."""
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
                    raise RecoveryExhaustedError(
                        f"❌ → '{action_name}' falló tras {retry_count} intentos."
                    ) from e

                if auto_refreshes < auto_refresh_limit:
                    auto_refreshes += 1
                    retry_count += 1
                    logger.info(
                        f"🔄 → Auto-refresh {auto_refreshes}/{auto_refresh_limit} "
                        f"para '{action_name}'..."
                    )
                    page.reload()
                    page.wait_for_load_state("networkidle")
                    continue

                action = self.wait_for_user_action(
                    f"Error en: {action_name}\nfalló: {e}\n"
                    f"(después de {auto_refresh_limit} auto-refreshes)",
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
        """Espera una acción del usuario a través de Telegram."""
        full_msg = (
            f"Batch: {self.batch_classes}\n\n"
            f"❌ → {error_description}.\n\n"
            "Responde\n\n"
            "0️⃣\tResume\n"
            "1️⃣\tRefresh & Retry\n\n"
            f"Intento #{retry_count}."
        )
        self._notifier.notify(full_msg)

        last_update_id = self._get_last_update_id()
        start = time.time()

        while time.time() - start < timeout:
            updates = self._notifier.get_updates()
            for update in updates.get("result", []):
                update_id = update["update_id"]
                if update_id <= last_update_id:
                    continue
                last_update_id = update_id

                text = update.get("message", {}).get("text", "").strip()
                if text == "0":
                    self._notifier.notify("▶️ → Resuming...")
                    return "resume"
                if text == "1":
                    self._notifier.notify("🔄 → Refreshing and retrying...")
                    return "refresh"

            time.sleep(5)

        self._notifier.notify("❌ → Timeout de recovery alcanzado. El bot se detendrá.")
        return "abort"

    def _handle_user_action(
        self,
        action: str,
        page: Page,
        action_name: str,
        retry_count: int,
        auto_refreshes: int,
    ) -> tuple[int, int]:
        """Ejecuta la acción del usuario y retorna (retry_count, auto_refreshes) actualizados."""
        if action == "resume":
            return retry_count + 1, 0
        elif action == "refresh":
            page.reload()
            page.wait_for_load_state("networkidle")
            return retry_count + 1, 0
        elif action == "abort":
            raise RecoveryAbortedError(f"❌ → Bot abortado durante '{action_name}'.")
        return retry_count, auto_refreshes

    def _get_last_update_id(self) -> int:
        """Obtiene el update_id más reciente para ignorar mensajes viejos."""
        updates = self._notifier.get_updates()
        results = updates.get("result", [])
        return results[-1]["update_id"] if results else 0
