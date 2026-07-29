"""Shared fixtures for gym-bot tests."""

from __future__ import annotations

from typing import Any

import pytest

from src.notifications import TelegramUpdatesResponse


class FakeNotifier:
    """In-memory fake that implements the Notifier protocol for testing."""

    def __init__(self) -> None:
        self.sent_messages: list[str] = []
        self._updates: list[dict[str, Any]] = []
        self._update_counter: int = 0

    def notify(self, msg: str) -> None:
        self.sent_messages.append(msg)

    def get_updates(self) -> TelegramUpdatesResponse:
        return {"result": list(self._updates)}

    def add_update(self, text: str) -> None:
        self._update_counter += 1
        self._updates.append(
            {
                "update_id": self._update_counter,
                "message": {"text": text},
            }
        )


@pytest.fixture
def fake_notifier() -> FakeNotifier:
    """Fixture that provides a FakeNotifier instance."""
    return FakeNotifier()
