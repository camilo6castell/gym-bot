"""
Configuración principal de la aplicación.

Carga y valida:
  - Variables de entorno (.env)               -> EnvSettings   (pydantic-settings)
  - src/config/schedule.yaml                  -> ScheduleConfig (pydantic)
  - src/config/app_config.yaml                -> AppConfig      (pydantic)

y expone todo a través de `Config`, que:
  * ofrece acceso TIPADO y moderno (settings.env.TOKEN,
    settings.app_config.os.home_user, settings.schedule.days, ...)
  * mantiene la interfaz PÚBLICA anterior (settings.env_vars,
    settings.get("CLAVE")) para no romper el resto del sistema.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.types.config import AppConfig, ConfigVars, ScheduleConfig

_ModelT = TypeVar("_ModelT", bound=BaseModel)


class EnvSettings(BaseSettings):
    """
    Variables de entorno de la aplicación.

    Pydantic-settings se encarga de: leer `.env`, convertir tipos y
    lanzar un error legible si falta alguna variable requerida — ya no
    hace falta un `_REQUIRED_ENV_VARS` recorrido a mano con `os.getenv`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Requeridas
    COMPENSAR_DOC_TYPE: str = Field(..., description="Tipo documento")
    COMPENSAR_DOC_NUM: str = Field(..., description="Número documento")
    COMPENSAR_PASSWORD: str = Field(..., description="Contraseña")
    TOKEN: str = Field(..., description="Token Telegram")
    CHAT_ID: str = Field(..., description="Chat ID Telegram")

    # Opcionales
    FIREFOX_PROFILE_NAME: str | None | None = None


class Settings:
    """
    Punto de acceso único a la configuración de la aplicación.

    Uso recomendado (nuevo código):
        settings.env.TOKEN
        settings.app_config.os.home_user
        settings.schedule.days["monday"]

    Uso heredado (código existente, se mantiene funcionando igual):
        settings.env_vars["TOKEN"]
        settings.get("TOKEN")
    """

    _BASE_DIR: Path = Path(__file__).resolve().parent
    _SCHEDULE_FILE: Path = _BASE_DIR / "schedule.yaml"
    _APP_CONFIG_FILE: Path = _BASE_DIR / "app_config.yaml"

    def __init__(self, env_file: str | None = None) -> None:
        # =========================
        # VARIABLES DE ENTORNO
        # =========================
        self.env: EnvSettings = (
            EnvSettings(_env_file=env_file) if env_file else EnvSettings()  # type: ignore[call-arg]
        )

        # =========================
        # CONFIGURACIONES YAML
        # =========================
        self.schedule: ScheduleConfig = self._load_yaml(self._SCHEDULE_FILE, ScheduleConfig)
        self.app_config: AppConfig = self._load_yaml(self._APP_CONFIG_FILE, AppConfig)

        # =========================
        # VALORES DERIVADOS
        # =========================
        self.home_user: str = os.path.expanduser(self.app_config.os.home_user)
        self.chromium_profile_path: str = os.path.join(self.home_user, ".config", "chromium")
        self.firefox_profile_path: str | None = (
            os.path.join(
                self.home_user,
                ".config",
                ".mozilla",
                "firefox",
                self.env.FIREFOX_PROFILE_NAME,
            )
            if self.env.FIREFOX_PROFILE_NAME
            else None
        )

        # Diccionario "plano" para compatibilidad con la interfaz pública anterior
        self._env_vars: ConfigVars = self._build_env_vars()

    # -----------------------------------------------------
    # Carga / validación de YAML
    # -----------------------------------------------------
    @staticmethod
    def _load_yaml(file_path: Path, model: type[_ModelT]) -> _ModelT:
        """Lee un YAML y lo valida contra un modelo Pydantic."""
        if not file_path.exists():
            raise FileNotFoundError(f"❌ Archivo de configuración no encontrado: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                raw = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"❌ Error leyendo archivo YAML '{file_path.name}': {e}") from e

        if not raw:
            raise ValueError(f"❌ El archivo YAML está vacío o mal formado: {file_path}")

        try:
            return model.model_validate(raw)
        except ValidationError as e:
            raise ValueError(f"❌ Configuración inválida en '{file_path.name}':\n{e}") from e

    # -----------------------------------------------------
    # Compatibilidad hacia atrás
    # -----------------------------------------------------
    def _build_env_vars(self) -> ConfigVars:
        data: ConfigVars = {
            "COMPENSAR_DOC_TYPE": self.env.COMPENSAR_DOC_TYPE,
            "COMPENSAR_DOC_NUM": self.env.COMPENSAR_DOC_NUM,
            "COMPENSAR_PASSWORD": self.env.COMPENSAR_PASSWORD,
            "TOKEN": self.env.TOKEN,
            "CHAT_ID": self.env.CHAT_ID,
            "SCHEDULE": self.schedule.model_dump(),
            "APP_CONFIG": self.app_config.model_dump(),
            "HOME_USER": self.home_user,
            "CHROMIUM_PROFILE_PATH": self.chromium_profile_path,
        }

        if self.env.FIREFOX_PROFILE_NAME and self.firefox_profile_path:
            data["FIREFOX_PROFILE_NAME"] = self.env.FIREFOX_PROFILE_NAME
            data["FIREFOX_PROFILE_PATH"] = self.firefox_profile_path

        return data

    @property
    def env_vars(self) -> ConfigVars:
        """Devuelve todas las variables de configuración cargadas (dict plano)."""
        return self._env_vars

    def get(self, key: str) -> Any:
        """Obtiene una variable de configuración por clave (interfaz heredada)."""
        value: Any = self._env_vars.get(key)
        if value is None:
            raise KeyError(f"Clave de configuración '{key}' no encontrada.")
        return value

    def _get_bool(self, key: str) -> bool:
        value = self._env_vars.get(key, "")
        return str(value).lower() in ("1", "true", "yes", "on")
