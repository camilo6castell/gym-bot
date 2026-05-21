import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from core.env_utils import (
    load_schedule,
    load_app_config,
)


class Config:
    def __init__(self, env_file: Optional[str] = None):

        # =========================
        # LOAD .ENV
        # =========================

        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        self._env_vars: Dict[str, Any] = {}

        # =========================
        # SENSITIVE ENV VARS
        # =========================

        required_env_vars = {
            "COMPENSAR_DOC_TYPE": "Tipo documento",
            "COMPENSAR_DOC_NUM": "Número documento",
            "COMPENSAR_PASSWORD": "Contraseña",
            "TOKEN": "Token Telegram",
            "CHAT_ID": "Chat ID Telegram",
        }

        for key, description in required_env_vars.items():
            value = os.getenv(key)

            if value is None:
                raise ValueError(
                    f"Variable requerida '{key}' no encontrada. " f"{description}"
                )

            self._env_vars[key] = value

        # =========================
        # OPTIONAL ENV VARS
        # =========================

        firefox_profile_name = os.getenv("FIREFOX_PROFILE_NAME")

        if firefox_profile_name:
            self._env_vars["FIREFOX_PROFILE_NAME"] = firefox_profile_name

        # =========================
        # YAML CONFIGS
        # =========================

        self._env_vars["SCHEDULE"] = load_schedule()

        app_config = load_app_config()

        self._env_vars["APP_CONFIG"] = app_config

        # =========================
        # DERIVED VALUES
        # =========================
        home_user = os.path.expanduser(app_config.get("os", {}).get("home_user", ""))

        self._env_vars["HOME_USER"] = home_user

        self._env_vars["CHROMIUM_PROFILE_PATH"] = os.path.join(
            home_user,
            ".config",
            "chromium",
        )

        if firefox_profile_name:
            self._env_vars["FIREFOX_PROFILE_PATH"] = os.path.join(
                home_user,
                ".config",
                ".mozilla",
                "firefox",
                firefox_profile_name,
            )

    @property
    def env_vars(self) -> Dict[str, Any]:
        return self._env_vars

    def get(self, key: str) -> Any:
        return self._env_vars.get(key)
