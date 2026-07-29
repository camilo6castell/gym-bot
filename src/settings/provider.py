"""
Main application configuration.

Loads and validates:
  - Environment variables (.env)        -> EnvSettings   (pydantic-settings)
  - src/config/schedule.yaml            -> ScheduleConfig (pydantic)
  - src/config/app_config.yaml          -> AppConfig      (pydantic)

Everything is exposed through typed attributes:
    settings.env.TOKEN
    settings.app_config.os.home_user
    settings.schedule.days["monday"]
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.types.config import AppConfig, ScheduleConfig

_ModelT = TypeVar("_ModelT", bound="BaseModel")


class EnvSettings(BaseSettings):
    """
    Application environment variables.

    pydantic-settings handles reading `.env`, type coercion, and raises a
    readable error if any required variable is missing.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required
    COMPENSAR_DOC_TYPE: str = Field(..., description="Document type")
    COMPENSAR_DOC_NUM: str = Field(..., description="Document number")
    COMPENSAR_PASSWORD: str = Field(..., description="Account password")
    TOKEN: str = Field(..., description="Telegram bot token")
    CHAT_ID: str = Field(..., description="Telegram chat ID")

    # Optional
    FIREFOX_PROFILE_NAME: str | None = None


class Settings:
    """
    Single access point for all application configuration.

    Usage:
        settings.env.TOKEN
        settings.app_config.os.home_user
        settings.schedule.days["monday"]
    """

    _BASE_DIR: Path = Path(__file__).resolve().parent
    _SCHEDULE_FILE: Path = _BASE_DIR / "schedule.yaml"
    _APP_CONFIG_FILE: Path = _BASE_DIR / "app_config.yaml"

    def __init__(self, env_file: str | None = None) -> None:
        self.env: EnvSettings = (
            EnvSettings(_env_file=env_file)  # type: ignore[call-arg]
            if env_file
            else EnvSettings()  # type: ignore[call-arg]
        )

        self.schedule: ScheduleConfig = self._load_yaml(self._SCHEDULE_FILE, ScheduleConfig)
        self.app_config: AppConfig = self._load_yaml(self._APP_CONFIG_FILE, AppConfig)

        self.home_user: str = os.path.expanduser(self.app_config.os.home_user)
        self.chromium_profile_path: str = os.path.join(self.home_user, ".config", "chromium")
        self.firefox_profile_path: str | None = (
            os.path.join(
                self.home_user,
                ".mozilla",
                "firefox",
                self.env.FIREFOX_PROFILE_NAME,
            )
            if self.env.FIREFOX_PROFILE_NAME
            else None
        )

    @staticmethod
    def _load_yaml(file_path: Path, model: type[_ModelT]) -> _ModelT:
        """Read a YAML file and validate it against a Pydantic model."""
        if not file_path.exists():
            raise FileNotFoundError(f"❌ Configuration file not found: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                raw = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"❌ Error reading YAML '{file_path.name}': {e}") from e

        if not raw:
            raise ValueError(f"❌ YAML file is empty or malformed: {file_path}")

        try:
            return model.model_validate(raw)
        except ValidationError as e:
            raise ValueError(f"❌ Invalid configuration in '{file_path.name}':\n{e}") from e
