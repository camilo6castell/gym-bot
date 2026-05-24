import os
from typing import Any, Optional, cast
from dotenv import load_dotenv
from pathlib import Path
from yaml import safe_load

from src.types.config import AppConfig, ConfigVars, ScheduleConfig


class Config:

    # Variables de entorno requeridas
    _REQUIRED_ENV_VARS: dict[str, str] = {
        "COMPENSAR_DOC_TYPE": "Tipo documento",
        "COMPENSAR_DOC_NUM": "Número documento",
        "COMPENSAR_PASSWORD": "Contraseña",
        "TOKEN": "Token Telegram",
        "CHAT_ID": "Chat ID Telegram",
    }

    # Archivos YAML
    _BASE_DIR: Path = Path(__file__).resolve().parent
    _SCHEDULE_FILE: Path = _BASE_DIR / "schedule.yaml"
    _APP_CONFIG_FILE: Path = _BASE_DIR / "app_config.yaml"
    _REQUIRED_CLASSES_SECTIONS: list[str] = ["timezone", "days"]
    _REQUIRED_APP_CONFIG_SECTIONS: list[str] = [
        "environment",
        "os",
        "selectors",
        "power_autonomous",
        "execution",
    ]

    def __init__(self, env_file: Optional[str] = None):
        # =========================
        # CARGA DE VARIABLES DE ENTORNO
        # =========================
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        self._env_vars: ConfigVars = {}

        # =========================
        # VARIABLES REQUERIDAS
        # =========================

        for key, description in self._REQUIRED_ENV_VARS.items():
            value = os.getenv(key)
            if value is None:
                raise ValueError(
                    f"Variable requerida '{key}' no encontrada. {description}"
                )
            self._env_vars[key] = value  # type: ignore[literal-required]

        # =========================
        # VARIABLES OPCIONALES
        # =========================
        firefox_profile_name = os.getenv("FIREFOX_PROFILE_NAME")
        if firefox_profile_name:
            self._env_vars["FIREFOX_PROFILE_NAME"] = firefox_profile_name

        # =========================
        # CARGA DE CONFIGURACIONES YAML
        # =========================
        self._env_vars["SCHEDULE"] = self._load_schedule_config(
            self._SCHEDULE_FILE,
            self._REQUIRED_CLASSES_SECTIONS,
        )

        self._env_vars["APP_CONFIG"] = self._load_app_config(
            self._APP_CONFIG_FILE,
            self._REQUIRED_APP_CONFIG_SECTIONS,
        )

        # =========================
        # VALORES DERIVADOS
        # =========================
        os_config = self._env_vars["APP_CONFIG"].get("os", {})
        home_user = os.path.expanduser(os_config.get("home_user", "~"))
        self._env_vars["HOME_USER"] = home_user

        self._env_vars["CHROMIUM_PROFILE_PATH"] = os.path.join(
            home_user, ".config", "chromium"
        )

        if firefox_profile_name:
            self._env_vars["FIREFOX_PROFILE_PATH"] = os.path.join(
                home_user, ".config", ".mozilla", "firefox", firefox_profile_name
            )

    def _load_yaml_raw(
        self, file_path: Path, required_sections: list[str]
    ) -> dict[str, Any]:
        """Lee y valida un archivo YAML, retorna el dict crudo"""
        if not file_path.exists():
            raise FileNotFoundError(
                f"❌ Archivo de configuración no encontrado: {file_path}"
            )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = cast(dict[str, Any], safe_load(f))
        except Exception as e:
            raise ValueError(f"❌ Error leyendo archivo YAML: {str(e)}")

        if not config:
            raise ValueError("❌ El archivo YAML está vacío o mal formado.")

        missing = [s for s in required_sections if s not in config]
        if missing:
            raise ValueError(
                f"❌ Configuración incompleta. Faltan secciones: {', '.join(missing)}"
            )

        return config

    def _load_schedule_config(
        self, file_path: Path, required_sections: list[str]
    ) -> ScheduleConfig:
        """Carga y valida el archivo schedule.yaml"""
        config = self._load_yaml_raw(file_path, required_sections)

        if not isinstance(config["days"], dict):
            raise ValueError("❌ 'days' debe ser un diccionario")

        return config  # type: ignore[return-value]

    def _load_app_config(
        self, file_path: Path, required_sections: list[str]
    ) -> AppConfig:
        """Carga y valida el archivo app_config.yaml"""
        config = self._load_yaml_raw(file_path, required_sections)
        return config  # type: ignore[return-value]

    @property
    def env_vars(self) -> ConfigVars:
        """Devuelve todas las variables de configuración cargadas"""
        return self._env_vars

    def get(self, key: str) -> Any:
        """Obtiene una variable de configuración por clave"""
        value: Any = self._env_vars.get(key)
        if value is None:
            raise KeyError(f"Clave de configuración '{key}' no encontrada.")
        return value

    def _get_bool(self, key: str) -> bool:
        value = self._env_vars.get(key, "")
        return str(value).lower() in ("1", "true", "yes", "on")
