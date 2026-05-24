from typing import Any, TypedDict

# =========================================================
# GENERIC
# =========================================================

YamlDict = dict[str, Any]


# =========================================================
# SCHEDULE CONFIG
# =========================================================


class GymClass(TypedDict):
    name: str
    hour: str


DaysConfig = dict[str, list[GymClass]]


class ForcedClass(TypedDict):
    name: str
    hour: str
    day: str


class ScheduleConfig(TypedDict, total=False):
    timezone: str
    days: DaysConfig
    forcedClass: ForcedClass


# =========================================================
# APP CONFIG
# =========================================================


class EnvironmentConfig(TypedDict):
    login_url: str
    inside_system_url: str
    gym_class_verification_url: str
    inside_system_url_pattern: str


class OSConfig(TypedDict, total=False):
    home_user: str
    firefox_path: str
    chromium_path: str


class SelectorsConfig(TypedDict, total=False):
    potential_modal_entiendo_selector: str
    potential_intermediate_login_selector: str


class PowerAutonomousConfig(TypedDict, total=False):
    wakealarm_path: str
    wake_minutes_before: int
    sleep_minutes_after: int


class ExecutionConfig(TypedDict, total=False):
    bot_force_run: bool
    execution_adjustment: int
    bot_headless: bool


class AppConfig(TypedDict, total=False):
    environment: EnvironmentConfig
    os: OSConfig
    selectors: SelectorsConfig
    power_autonomous: PowerAutonomousConfig
    execution: ExecutionConfig


# =========================================================
# ROOT CONFIG (env_vars dict en Config)
# =========================================================


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

    # YAML CONFIGS
    SCHEDULE: ScheduleConfig
    APP_CONFIG: AppConfig

    # DERIVED VALUES
    HOME_USER: str
    CHROMIUM_PROFILE_PATH: str
    FIREFOX_PROFILE_PATH: str
