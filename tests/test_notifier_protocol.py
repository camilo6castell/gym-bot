"""Tests that TelegramClient and FakeNotifier satisfy the Notifier protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.notifications import TelegramUpdatesResponse
from tests.conftest import FakeNotifier


@runtime_checkable
class _NotifierCheck(Protocol):
    def notify(self, msg: str) -> None: ...
    def get_updates(self) -> TelegramUpdatesResponse: ...


class TestNotifierProtocol:
    def test_fake_notifier_satisfies_protocol(self) -> None:
        assert isinstance(FakeNotifier(), _NotifierCheck)

    def test_fake_notifier_sends_messages(self) -> None:
        notifier = FakeNotifier()
        notifier.notify("Hello")

        assert len(notifier.sent_messages) == 1
        assert notifier.sent_messages[0] == "Hello"

    def test_fake_notifier_returns_updates(self) -> None:
        notifier = FakeNotifier()
        notifier.add_update("0")

        updates = notifier.get_updates()
        assert len(updates["result"]) == 1
        assert updates["result"][0]["message"]["text"] == "0"
