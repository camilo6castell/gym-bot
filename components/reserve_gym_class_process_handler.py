from core.config import Config
from playwright.sync_api import Page
from components.day_selector_handler import (
    perform_select_by_day,
    perform_select_latest_date,
)
from components.gym_class_booker_handler import perform_gym_class_booker
from components.membership_handler import perform_open_plan_and_use_membership
from utils.page_utils import confirm_url
from utils.logger import logger

app_config = Config(env_file=".env").get("APP_CONFIG")

config_environment = app_config.get("environment", {})
config_selectors = app_config.get("selectors", {})
config_execution = app_config.get("execution", {})


def perform_reserve_gym_class(
    page: Page,
    spanish_day_name: str,
    gym_class_name: str,
    gym_class_hour: str,
) -> bool:

    # Siempre parte desde la URL base
    confirm_url(
        page,
        config_environment.get("inside_system_url"),
    )

    perform_open_plan_and_use_membership(page)

    day_selected = (
        perform_select_by_day(page, spanish_day_name)
        if config_execution.get("BOT_FORCE_RUN")
        else perform_select_latest_date(page)
    )

    if not day_selected:
        logger.warning(f"⚠️ → Día '{spanish_day_name}' no encontrado, saltando.")
        return False

    perform_gym_class_booker(
        page,
        gym_class_name,
        gym_class_hour,
    )
    return True
