from pathlib import Path
from typing import Any
import requests
from src.utils.logger import logger
from src.config.config import Config

_config = Config(env_file=str(Path(__file__).resolve().parent.parent / ".env"))
_BASE_URL = f"https://api.telegram.org/bot{_config.get('TOKEN')}"


def notify(msg: str) -> None:
    try:
        requests.post(
            f"{_BASE_URL}/sendMessage",
            json={"chat_id": _config.get("CHAT_ID"), "text": msg},
            timeout=10,
        )
    except Exception as e:
        logger.warning(f"notify falló: {e}")


def getUpdates() -> dict[str, Any]:
    try:
        response = requests.get(f"{_BASE_URL}/getUpdates", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"getUpdates falló: {e}")
        return {"result": []}
