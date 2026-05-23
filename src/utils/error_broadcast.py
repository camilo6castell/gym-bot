import time
from pathlib import Path
from playwright.sync_api import Page
from src.utils.logger import logger
from src.notifications.telegram import notify

DEBUG_DIR = Path(__file__).resolve().parent.parent.parent / "debug"
DEBUG_DIR.mkdir(exist_ok=True)


def send_error_broadcast(page: Page, error_message: str) -> None:
    notify(f"❌ → {error_message}")
    logger.error(f"❌ → {error_message}")
    screenshot_path = DEBUG_DIR / f"error_{int(time.time())}.png"
    try:
        page.screenshot(path=str(screenshot_path))
        logger.debug(f"📸 → Screenshot guardado: {screenshot_path}")
    except Exception as e:
        logger.debug(f"📸 → No se pudo guardar screenshot: {e}")
