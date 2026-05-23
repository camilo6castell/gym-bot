import os
from typing import Dict, Any, Optional
from xmlrpc.client import boolean
from dotenv import load_dotenv
from pathlib import Path
from yaml import safe_load


class Config:

    # Variables de entorno requeridas
    _REQUIRED_ENV_VARS: Dict[str, str] = {
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

        self._env_vars: Dict[str, Any] = {}

        # =========================
        # VARIABLES REQUERIDAS
        # =========================

        for key, description in self._REQUIRED_ENV_VARS.items():
            value = os.getenv(key)
            if value is None:
                raise ValueError(
                    f"Variable requerida '{key}' no encontrada. {description}"
                )
            self._env_vars[key] = value

        # =========================
        # VARIABLES OPCIONALES
        # =========================
        firefox_profile_name = os.getenv("FIREFOX_PROFILE_NAME")
        if firefox_profile_name:
            self._env_vars["FIREFOX_PROFILE_NAME"] = firefox_profile_name

        # =========================
        # CARGA DE CONFIGURACIONES YAML
        # =========================
        self._env_vars["SCHEDULE"] = self._load_yaml_config(
            self._SCHEDULE_FILE,
            self._REQUIRED_CLASSES_SECTIONS,
        )

        self._env_vars["APP_CONFIG"] = self._load_yaml_config(
            self._APP_CONFIG_FILE,
            self._REQUIRED_APP_CONFIG_SECTIONS,
        )

        # =========================
        # VALORES DERIVADOS
        # =========================
        home_user = os.path.expanduser(
            self._env_vars["APP_CONFIG"]["os"].get("home_user", "~")
        )
        self._env_vars["HOME_USER"] = home_user

        self._env_vars["CHROMIUM_PROFILE_PATH"] = os.path.join(
            home_user, ".config", "chromium"
        )

        if firefox_profile_name:
            self._env_vars["FIREFOX_PROFILE_PATH"] = os.path.join(
                home_user, ".config", ".mozilla", "firefox", firefox_profile_name
            )

    def _load_yaml_config(
        self, file_path: Path, required_sections: list[str]
    ) -> Dict[str, Any]:
        """Carga y valida un archivo YAML con secciones requeridas"""
        if not file_path.exists():
            raise FileNotFoundError(
                f"❌ Archivo de configuración no encontrado: {file_path}"
            )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = safe_load(f)
        except Exception as e:
            raise ValueError(f"❌ Error leyendo archivo YAML: {str(e)}")

        if not config:
            raise ValueError("❌ El archivo YAML está vacío o mal formado.")

        # Verificar secciones requeridas
        missing = [s for s in required_sections if s not in config]
        if missing:
            raise ValueError(
                f"❌ Configuración incompleta. Faltan secciones: {', '.join(missing)}"
            )

        # Validar estructura de 'days'
        if "days" in config and not isinstance(config["days"], dict):
            raise ValueError("❌ 'days' debe ser un diccionario")

        return config

    @property
    def env_vars(self) -> Dict[str, Any]:
        """Devuelve todas las variables de configuración cargadas"""
        return self._env_vars

    def get(self, key: str) -> Any:
        """Obtiene una variable de configuración por clave"""
        value: str | boolean | None = self._env_vars.get(key)
        if value is None:
            raise KeyError(f"Clave de configuración '{key}' no encontrada.")
        return value

    def _get_bool(self, key: str) -> bool:
        value = self._env_vars.get(key, "")
        return str(value).lower() in ("1", "true", "yes", "on")
