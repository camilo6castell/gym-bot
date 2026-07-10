"""
Modelos Pydantic que describen la configuración de la aplicación.

Estos modelos reemplazan los antiguos TypedDict: además de documentar la
forma de los datos, ahora los VALIDAN (tipos, campos requeridos, valores
permitidos) en el momento en que se cargan los archivos YAML / variables
de entorno.
"""

from typing import Any, Literal, TypedDict

from pydantic import BaseModel, ConfigDict

# =========================================================
# GENERIC
# =========================================================

YamlDict = dict[str, Any]

Weekday = Literal[
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class _StrictModel(BaseModel):
    """Base común: prohíbe campos desconocidos en los YAML (typos, etc.)."""

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
    forcedClass: ForcedClass | None = None


# =========================================================
# APP CONFIG (app_config.yaml)
# =========================================================


class EnvironmentConfig(_StrictModel):
    login_url: str
    inside_system_url: str
    gym_class_verification_url: str
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


class AppConfig(_StrictModel):
    environment: EnvironmentConfig
    os: OSConfig
    selectors: SelectorsConfig
    power_autonomous: PowerAutonomousConfig
    execution: ExecutionConfig


# =========================================================
# ROOT CONFIG (dict que expone Config.env_vars / Config.get)
# =========================================================
#
# Se conserva como TypedDict (no como modelo Pydantic) porque su único
# propósito es tipar el diccionario "plano" que se expone por compatibilidad
# hacia el resto del sistema (Config.env_vars / Config.get(key)).


class ConfigVars(TypedDict, total=False):
    # ENV VARS — credenciales
    COMPENSAR_DOC_TYPE: str
    COMPENSAR_DOC_NUM: str
    COMPENSAR_PASSWORD: str

    # ENV VARS — Telegram
    TOKEN: str
    CHAT_ID: str

    # ENV VARS — opcionales
    FIREFOX_PROFILE_NAME: str

    # YAML CONFIGS (dict "plano", ver Config._build_env_vars)
    SCHEDULE: YamlDict
    APP_CONFIG: YamlDict

    # DERIVED VALUES
    HOME_USER: str
    CHROMIUM_PROFILE_PATH: str
    FIREFOX_PROFILE_PATH: str
