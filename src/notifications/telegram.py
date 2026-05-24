from typing import Any, TypedDict, cast
import requests

from src.utils.logger import logger
from src.config.config import Config


class TelegramUpdatesResponse(TypedDict):
    result: list[dict[str, Any]]


_config = Config()
_BASE_URL = f"https://api.telegram.org/bot{_config.get('TOKEN')}"


def notify(msg: str) -> None:
    try:
        requests.post(
            f"{_BASE_URL}/sendMessage",
            json={
                "chat_id": _config.get("CHAT_ID"),
                "text": msg,
            },
            timeout=10,
        )
    except requests.RequestException as e:
        logger.warning(f"notify falló: {e}")


def getUpdates() -> TelegramUpdatesResponse:
    try:
        response = requests.get(
            f"{_BASE_URL}/getUpdates",
            timeout=10,
        )

        response.raise_for_status()

        return cast(TelegramUpdatesResponse, response.json())

    except requests.RequestException as e:
        logger.warning(f"getUpdates falló: {e}")
        return {"result": []}
