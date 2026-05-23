from playwright.sync_api import Page
from src.config.config import Config
from src.utils.logger import logger
from src.utils.page_utils import confirm_url
from src.components.membership import perform_open_plan_and_use_membership
from src.components.day_selector import (
    perform_select_by_day,
    perform_select_latest_date,
)
from src.components.gym_class_booker import perform_gym_class_booker

_config = Config()
_env = _config.get("APP_CONFIG").get("environment", {})
_execution = _config.get("APP_CONFIG").get("execution", {})


def perform_reserve_gym_class(
    page: Page,
    spanish_day_name: str,
    gym_class_name: str,
    gym_class_hour: str,
) -> bool:
    confirm_url(page, _env.get("inside_system_url"))

    perform_open_plan_and_use_membership(page)

    day_selected = (
        perform_select_by_day(page, spanish_day_name)
        if _execution.get("bot_force_run")
        else perform_select_latest_date(page)
    )

    if not day_selected:
        logger.warning(f"⚠️ → Día '{spanish_day_name}' no encontrado, saltando.")
        return False

    perform_gym_class_booker(page, gym_class_name, gym_class_hour)
    return True
