"""Tests for the Recovery class with a FakeNotifier."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.utils.exceptions import RecoveryExhaustedError
from src.utils.recovery import Recovery


class TestRecoverySoft:
    def test_successful_action_returns_immediately(self, fake_notifier) -> None:
        recovery = Recovery(fake_notifier)
        recovery.with_soft_recovery(lambda: None, Mock(), "test")

        assert len(fake_notifier.sent_messages) == 0

    def test_retries_on_failure_then_succeeds(self, fake_notifier) -> None:
        recovery = Recovery(fake_notifier)
        call_count = 0

        def flaky_action() -> None:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Transient error")

        page_mock = Mock()
        recovery.with_soft_recovery(flaky_action, page_mock, "flaky", ms_to_retry=1, max_retries=3)

        assert call_count == 2

    def test_exhausts_retries_and_raises(self, fake_notifier) -> None:
        recovery = Recovery(fake_notifier)

        def always_fails() -> None:
            raise ValueError("Always fails")

        page_mock = Mock()

        with pytest.raises(RecoveryExhaustedError) as exc_info:
            recovery.with_soft_recovery(
                always_fails, page_mock, "will-fail", ms_to_retry=1, max_retries=2
            )

        assert "will-fail" in str(exc_info.value)


class TestRecoveryWaitForUserAction:
    def test_returns_resume_on_zero(self, fake_notifier, monkeypatch) -> None:
        recovery = Recovery(fake_notifier)
        # Bypass _get_last_update_id so the polling loop sees the update
        monkeypatch.setattr(recovery, "_get_last_update_id", lambda: 0)
        fake_notifier.add_update("0")

        result = recovery.wait_for_user_action("test error", timeout=5, retry_count=0)

        assert result == "resume"
        assert any("Resuming" in msg for msg in fake_notifier.sent_messages)

    def test_returns_refresh_on_one(self, fake_notifier, monkeypatch) -> None:
        recovery = Recovery(fake_notifier)
        monkeypatch.setattr(recovery, "_get_last_update_id", lambda: 0)
        fake_notifier.add_update("1")

        result = recovery.wait_for_user_action("test error", timeout=5, retry_count=0)

        assert result == "refresh"
        assert any("Refreshing" in msg for msg in fake_notifier.sent_messages)

    def test_returns_abort_on_timeout(self, fake_notifier) -> None:
        recovery = Recovery(fake_notifier)

        result = recovery.wait_for_user_action("test error", timeout=1, retry_count=0)

        assert result == "abort"


class TestRecoveryHandleUserAction:
    def test_resume_increments_retry_count(self, fake_notifier) -> None:
        recovery = Recovery(fake_notifier)
        page_mock = Mock()

        retry_count, auto_refreshes = recovery._handle_user_action(
            "resume", page_mock, "test", 0, 0
        )

        assert retry_count == 1
        assert auto_refreshes == 0

    def test_refresh_reloads_page(self, fake_notifier) -> None:
        recovery = Recovery(fake_notifier)
        page_mock = Mock()

        retry_count, auto_refreshes = recovery._handle_user_action(
            "refresh", page_mock, "test", 0, 0
        )

        assert retry_count == 1
        assert auto_refreshes == 0
        page_mock.reload.assert_called_once()

    def test_abort_raises_error(self, fake_notifier) -> None:
        recovery = Recovery(fake_notifier)
        page_mock = Mock()

        with pytest.raises(Exception) as exc_info:
            recovery._handle_user_action("abort", page_mock, "test", 0, 0)

        assert "aborted" in str(exc_info.value)
