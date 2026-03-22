from playwright.sync_api import Page
from bot.day_selector_handler import select_by_day, select_latest_date
from bot.gym_class_selector_handler import gym_class_selector
from components.membership import open_plan_and_use_membership
from utils.page_utils import confirm_url
from utils.logger import logger


def reserve_gym_class_handler(
    page: Page,
    post_login_url,
    spanish_day_name,
    is_force_run: bool,
    gym_class_name: str,
    gym_class_hour: str,
):
    # Siempre parte desde la URL base
    confirm_url(
        page,
        post_login_url,
    )

    open_plan_and_use_membership(page)

    day_selected = (
        select_by_day(page, spanish_day_name)
        if is_force_run
        else select_latest_date(page)
    )

    if not day_selected:
        logger.warning(f"⚠️ Día '{spanish_day_name}' no encontrado, saltando.")
        return False

    gym_class_selector(page, gym_class_name, gym_class_hour)
    return True
