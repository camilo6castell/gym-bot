"""
Pydantic models describing the application configuration.

These models replace the old TypedDict approach: they VALIDATE the data
(types, required fields, allowed values) at load time rather than deferring
errors to runtime.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

# =========================================================
# GENERIC
# =========================================================

Weekday = Literal[
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class RunDevice(StrEnum):
    """
    Device profile used to launch Chromium via Playwright.

    `DESKTOP` uses the real window size; the mobile members emulate a phone
    through Playwright's built-in device descriptors (viewport, user agent,
    touch events). Values must match Playwright's device names.
    """

    DESKTOP = "desktop"
    GALAXY_S24 = "Galaxy S24"
    IPHONE_15_PRO_MAX = "iPhone 15 Pro Max"


class _StrictModel(BaseModel):
    """Common base: forbid extra fields in YAML (catches typos early)."""

    model_config = ConfigDict(extra="forbid")


# =========================================================
# SCHEDULE CONFIG (schedule.yaml)
# =========================================================


class GymClass(_StrictModel):
    name: str
    hour: str


class ForcedClass(_StrictModel):
    name: str
    hour: str
    day: Weekday


DaysConfig = dict[Weekday, list[GymClass]]


class ScheduleConfig(_StrictModel):
    timezone: str
    days: DaysConfig
    forced_class: ForcedClass | None = None


ScheduledClass = ForcedClass


# =========================================================
# APP CONFIG (app_config.yaml)
# =========================================================


class EnvironmentConfig(_StrictModel):
    login_url: str
    inside_system_url: str
    inside_system_url_pattern: str


class OSConfig(_StrictModel):
    home_user: str = "~"
    firefox_path: str | None = None
    chromium_path: str | None = None


class SelectorsConfig(_StrictModel):
    potential_temporary_platform_notification: str | None = None
    potential_modal_entiendo_selector: str | None = None
    potential_intermediate_login_selector: str | None = None


class PowerAutonomousConfig(_StrictModel):
    wakealarm_path: str | None = None
    wake_minutes_before: int = 5
    sleep_minutes_after: int = 10


class ExecutionConfig(_StrictModel):
    bot_force_run: bool = False
    seconds_for_temporary_platform_notifications: int | None = None
    execution_adjustment: int = 0
    bot_headless: bool = False
    run_device: RunDevice = RunDevice.DESKTOP


class AppConfig(_StrictModel):
    environment: EnvironmentConfig
    os: OSConfig
    selectors: SelectorsConfig
    power_autonomous: PowerAutonomousConfig
    execution: ExecutionConfig
