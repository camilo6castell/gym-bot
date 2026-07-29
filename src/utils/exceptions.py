"""
Domain-specific exception hierarchy for gym-bot.

Using specific exceptions (instead of generic `RuntimeError`/`ValueError`)
lets upper layers (`Recovery`, `main.py`) distinguish what failed and
decide how to react, while leaving more readable error traces.
"""

from __future__ import annotations


class GymBotError(Exception):
    """Base exception for all application domain errors."""


class CaptchaDetectedError(GymBotError):
    """Raised when an active CAPTCHA requiring human intervention is detected."""


class BrowserLaunchError(GymBotError):
    """Raised when the browser cannot start due to missing configuration or environment."""


class ElementNotFoundError(GymBotError):
    """Raised when a required page element does not appear within the timeout."""


class RedirectTimeoutError(GymBotError):
    """Raised when the page does not redirect to the expected URL within the timeout."""


class MembershipNotFoundError(GymBotError):
    """Raised when no membership/ticket buttons are available or enabled."""


class ReservationVerificationError(GymBotError):
    """Raised when a class reservation cannot be confirmed."""


class ScheduleConfigError(GymBotError):
    """Raised when the schedule configuration is invalid or incomplete."""


class RecoveryExhaustedError(GymBotError):
    """Raised when an action exhausts its automatic retries without recovering."""


class RecoveryAbortedError(GymBotError):
    """Raised when the user aborts the flow during assisted recovery."""
