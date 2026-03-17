import time

from notifications.telegram import notify
from utils.logger import logger


def send_error_broadcast(page, error_message):
    notify(f"❌ {error_message}")
    logger.error(f"❌ {error_message}")
    page.screenshot(path=f"debug/error_{int(time.time())}.png")
