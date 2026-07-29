from __future__ import annotations

from typing import Any, Protocol, TypedDict


class TelegramUpdatesResponse(TypedDict):
    result: list[dict[str, Any]]


class Notifier(Protocol):
    """Interface for sending notifications and polling for remote commands."""

    def notify(self, msg: str) -> None: ...

    def get_updates(self) -> TelegramUpdatesResponse: ...
