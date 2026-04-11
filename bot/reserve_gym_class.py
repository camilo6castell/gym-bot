from playwright.sync_api import Page
from bot.day_selector_handler import select_by_day, select_latest_date
from bot.gym_class_selector_handler import gym_class_selector
from components.membership import open_plan_and_use_membership
from utils.page_utils import confirm_url
from utils.logger import logger


def perform_reserve_gym_class(
    page: Page,
    INSIDE_SYSTEM_URL_PATTERN,
    spanish_day_name,
    BOT_FORCE_RUN: bool,
    gym_class_name: str,
    gym_class_hour: str,

) -> bool:

    # Siempre parte desde la URL base
    confirm_url(
        page,
        INSIDE_SYSTEM_URL_PATTERN,
    )

    open_plan_and_use_membership(page)

    day_selected = (
        select_by_day(page, spanish_day_name)
        if BOT_FORCE_RUN
        else select_latest_date(page)
    )

    if not day_selected:
        logger.warning(f"⚠️ → Día '{spanish_day_name}' no encontrado, saltando.")
        return False

    gym_class_selector(
        page,
        gym_class_name,
        gym_class_hour,
    )
    return True
