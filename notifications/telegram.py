import requests
from typing import Any
from utils.logger import logger
from core.config import Config

config = Config(env_file=".env")


def notify(msg: str):
    try:
        url = f"https://api.telegram.org/bot{config.get('TOKEN')}/sendMessage"
        _ = requests.post(
            url, json={"chat_id": config.get("CHAT_ID"), "text": msg}, timeout=10
        )
    except Exception as e:
        logger.warning(f"notify falló: {e}")


def getUpdates() -> dict[str, Any]:
    try:
        url = f"https://api.telegram.org/bot{config.get('TOKEN')}/getUpdates"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"getUpdates falló: {e}")
        return {"result": []}  # retorna vacío, no rompe el loop
