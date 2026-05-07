import time
from playwright._impl._page import Page
from notifications.telegram import notify
from utils.logger import logger


async def send_error_broadcast(page: Page, error_message: str):
    notify(f"❌ → {error_message}")
    logger.error(f"❌ → {error_message}")
    await page.screenshot(path=f"debug/error_{int(time.time())}.png")
