"""
Error recovery mechanisms for browser automation.

`Recovery` receives its notifier through constructor injection (dependency
inversion), making it testable with a fake notifier.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from src.notifications import Notifier
from src.types.browser import IPage
from src.utils.exceptions import CaptchaDetectedError, RecoveryAbortedError, RecoveryExhaustedError
from src.utils.logger import logger


class Recovery:
    """
    Executes automation actions with layered recovery strategies.

    `with_soft_recovery`: automatic retry loop for transient failures.
    `with_recovery`: full pipeline with page reload, CAPTCHA handling, and
    remote command polling via the injected `Notifier`.
    """

    def __init__(self, notifier: Notifier) -> None:
        self._notifier = notifier
        self.batch_classes: list[dict[str, str]] | None = None

    def set_batch_classes(self, batch_classes: list[dict[str, str]]) -> None:
        """Set the current batch class list (used as context in recovery notifications)."""
        self.batch_classes = batch_classes

    def with_soft_recovery(
        self,
        action_fn: Callable[[], Any],
        page: IPage,
        action_name: str = "please specify an action name",
        ms_to_retry: int = 3000,
        max_retries: int = 3,
    ) -> None:
        """Execute an action with automatic retry on failure.

        The first attempt runs immediately without waiting. Each subsequent
        retry waits an additional `ms_to_retry`: the second attempt waits
        `ms_to_retry`, the third waits `2 * ms_to_retry`, and so on.
        """
        attempts = 0
        last_exception: Exception | None = None

        while attempts <= max_retries:
            try:
                action_fn()
                return
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                last_exception = e
                attempts += 1
                remaining = max_retries - attempts
                logger.error(
                    f"❌ → '{action_name}' failed. Remaining retries: {remaining}. Error: {e}"
                )
                if attempts > max_retries:
                    break
                wait_ms = ms_to_retry * attempts
                logger.info(f"⏳ → Retrying in {wait_ms}ms...")
                page.wait_for_timeout(wait_ms)

        raise RecoveryExhaustedError(
            f"❌ → '{action_name}' failed after {max_retries} retries. Last error: {last_exception}"
        )

    def with_recovery(
        self,
        action_fn: Callable[[], Any],
        page: IPage,
        action_name: str = "action",
        max_retries: int | None = 3,
        auto_refresh_limit: int = 2,
    ) -> None:
        """Execute an action with advanced recovery:
        retry loop, CAPTCHA handling, remote commands."""
        retry_count = 0
        auto_refreshes = 0

        while True:
            try:
                action_fn()
                return

            except CaptchaDetectedError:
                logger.warning(f"🔒 → CAPTCHA on '{action_name}', requesting help...")
                action = self.wait_for_user_action(
                    f"🔒 → CAPTCHA detected in: {action_name}\nSolve it and reply.",
                    timeout=600,
                    retry_count=retry_count,
                )
                retry_count, auto_refreshes = self._handle_user_action(
                    action, page, action_name, retry_count, auto_refreshes
                )

            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                logger.error(f"❌ → Error in '{action_name}': {e}")

                if max_retries is not None and retry_count >= max_retries:
                    raise RecoveryExhaustedError(
                        f"❌ → '{action_name}' failed after {retry_count} retries."
                    ) from e

                if auto_refreshes < auto_refresh_limit:
                    auto_refreshes += 1
                    retry_count += 1
                    logger.info(
                        f"🔄 → Auto-refresh {auto_refreshes}/{auto_refresh_limit} "
                        f"for '{action_name}'..."
                    )
                    page.reload()
                    page.wait_for_load_state("networkidle")
                    continue

                action = self.wait_for_user_action(
                    f"Error in: {action_name}\nfailed: {e}\n"
                    f"(after {auto_refresh_limit} auto-refreshes)",
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
        """Wait for a remote user command via the notifier."""
        full_msg = (
            f"Batch: {self.batch_classes}\n\n"
            f"❌ → {error_description}.\n\n"
            "Reply\n\n"
            "0️⃣\tResume\n"
            "1️⃣\tRefresh & Retry\n\n"
            f"Attempt #{retry_count}."
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

        self._notifier.notify("❌ → Recovery timeout reached. Bot will stop.")
        return "abort"

    def _handle_user_action(
        self,
        action: str,
        page: IPage,
        action_name: str,
        retry_count: int,
        auto_refreshes: int,
    ) -> tuple[int, int]:
        """Execute the user action and return updated (retry_count, auto_refreshes)."""
        if action == "resume":
            return retry_count + 1, 0
        elif action == "refresh":
            page.reload()
            page.wait_for_load_state("networkidle")
            return retry_count + 1, 0
        elif action == "abort":
            raise RecoveryAbortedError(f"❌ → Bot aborted during '{action_name}'.")
        return retry_count, auto_refreshes

    def _get_last_update_id(self) -> int:
        """Get the most recent update_id to ignore already-processed messages."""
        updates = self._notifier.get_updates()
        results = updates.get("result", [])
        return results[-1]["update_id"] if results else 0
