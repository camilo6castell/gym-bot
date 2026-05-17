# core/config.py
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from .env_utils import env_bool  # Asegúrate de importar env_bool


class Config:
    def __init__(self, env_file: Optional[str] = None):
        # Carga variables desde .env si existe
        if env_file:
            load_dotenv(env_file)

        # Mapeo de variables de entorno a atributos
        self._env_vars: Dict[str, Any] = {}
        self._required_vars: Dict[str, str] = {
            "COMPENSAR_DOC_TYPE": "Tipo de documento (ej.: 'DNI')",
            "COMPENSAR_DOC_NUM": "Número de documento",
            "COMPENSAR_PASSWORD": "Contraseña",
            "LOGIN_URL": "URL de inicio de sesión",
            "POST_LOGIN_URL": "URL después del login",
            "GYM_CLASS_VERIFICATION_URL": "URL para verificar reservas",
            "POTENTIAL_MODAL_ENTIENDO_SELECTOR": "Selector para modal 'Entiendo'",
            "POTENTIAL_INTERMEDIATE_LOGIN_SELECTOR": "Selector para login intermedio",
            "INSIDE_SYSTEM_URL": "URL base dentro del sistema",
            "INSIDE_SYSTEM_URL_PATTERN": "Patrón de URL para clases",
            "BOT_FORCE_RUN": "Forzar ejecución de clases",
            "BOT_FORCE_RUN_CLASS": "Clase específica para forzar",
            "BOT_FORCE_RUN_HOUR": "Hora para forzar",
            "BOT_FORCE_RUN_DAY": "Día para forzar",
            "ADDITIONAL_MINUTE_FOR_EXECUTION": "Minutos adicionales para ejecución",
            "BOT_HEADLESS": "Ejecutar en modo headless",
            "WAKE_MINUTES_BEFORE": "Minutos antes de despertar",
            "SLEEP_MINUTES_AFTER": "Minutos después de dormir",
            "WAKEALARM_PATH": "Ruta del wakealarm",
            "TOKEN": "Token de notificación",
            "CHAT_ID": "ID del chat",
            "HOME_USER": "Usuario home para rutas relativas",
            "FIREFOX_PATH": "Ruta del ejecutable de Firefox",
            "CHROMIUM_PATH": "Ruta del ejecutable de Chromium",
        }

        # Carga todas las variables de entorno
        for key, description in self._required_vars.items():
            value = os.getenv(key)
            if value is None:
                raise ValueError(
                    f"Variable de entorno '{key}' requerida pero no encontrada. {description}"
                )
            # Aplica conversiones según el tipo
            if key in [
                "BOT_FORCE_RUN",
                "ADDITIONAL_MINUTE_FOR_EXECUTION",
                "BOT_HEADLESS",
            ]:
                self._env_vars[key] = env_bool(value)
            elif key == "HOME_USER":
                self._env_vars[key] = os.path.expanduser(value)
                self._env_vars["CHROMIUM_PROFILE_PATH"] = os.path.join(
                    self._env_vars[key], ".config", "chromium"
                )

                firefox_profile_name = os.getenv("FIREFOX_PROFILE_NAME")
                if firefox_profile_name is not None:
                    self._env_vars["FIREFOX_PROFILE_PATH"] = os.path.join(
                        self._env_vars[key],
                        ".config",
                        ".mozilla",
                        "firefox",
                        firefox_profile_name,
                    )
            else:
                self._env_vars[key] = value

    @property
    def env_vars(self) -> Dict[str, Any]:
        """Devuelve todas las variables de entorno cargadas"""
        return self._env_vars

    def get(self, key: str) -> Any:
        """Accede a una variable específica"""
        return self._env_vars.get(key)
