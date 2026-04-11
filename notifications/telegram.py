import requests
from utils.logger import logger
from core.env import TOKEN, CHAT_ID


def notify(msg: str):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        _ = requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        logger.warning(f"notify falló: {e}")


def getUpdates():
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"getUpdates falló: {e}")
        return {"result": []}  # retorna vacío, no rompe el loop
