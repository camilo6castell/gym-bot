from typing import Any, TypedDict, cast

import requests

from src.utils.logger import logger


class TelegramUpdatesResponse(TypedDict):
    result: list[dict[str, Any]]


class TelegramClient:
    """
    Encapsulates interactions with the Telegram Bot API.

    The client uses a `Config` instance to retrieve the bot token and chat ID,
    and exposes methods for sending messages (`notify`) and retrieving updates
    (`get_updates`).  All network calls are wrapped in try/except blocks that
    log failures via `logger`.
    """

    def __init__(self, token: str, chat_id: str) -> None:
        """
        Create a new client.

        Parameters
        ----------
        token : str
            The bot token for API authentication.
        chat_id : str
            The ID of the chat to send messages to.
        """
        # Base URL for all API calls (e.g. https://api.telegram.org/bot<token>)
        self.base_url = f"https://api.telegram.org/bot{token}"
        self._chat_id = chat_id

    def notify(self, msg: str) -> None:
        """
        Send a message to the configured chat.

        Parameters
        ----------
        msg : str
            The text to send.
        """
        try:
            requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self._chat_id,
                    "text": msg,
                },
                timeout=10,
            )
        except requests.RequestException as e:
            logger.warning(f"notify falló: {e}")

    def get_updates(self) -> TelegramUpdatesResponse:
        """
        Retrieve pending updates from the bot.

        Returns
        -------
        TelegramUpdatesResponse
            A typed dictionary containing a list of update objects.
            On failure, returns an empty result list.
        """
        try:
            response = requests.get(
                f"{self.base_url}/getUpdates",
                timeout=10,
            )
            response.raise_for_status()
            return cast(TelegramUpdatesResponse, response.json())
        except requests.RequestException as e:
            logger.warning(f"get_updates falló: {e}")
            return {"result": []}


# from typing import Any, TypedDict, cast
# import requests

# from src.utils.logger import logger
# from src.config.config import Config


# class TelegramUpdatesResponse(TypedDict):
#     result: list[dict[str, Any]]


# _config = Config()
# _BASE_URL = f"https://api.telegram.org/bot{_config.get('TOKEN')}"


# def notify(msg: str) -> None:
#     try:
#         requests.post(
#             f"{_BASE_URL}/sendMessage",
#             json={
#                 "chat_id": _config.get("CHAT_ID"),
#                 "text": msg,
#             },
#             timeout=10,
#         )
#     except requests.RequestException as e:
#         logger.warning(f"notify falló: {e}")


# def getUpdates() -> TelegramUpdatesResponse:
#     try:
#         response = requests.get(
#             f"{_BASE_URL}/getUpdates",
#             timeout=10,
#         )

#         response.raise_for_status()

#         return cast(TelegramUpdatesResponse, response.json())

#     except requests.RequestException as e:
#         logger.warning(f"getUpdates falló: {e}")
#         return {"result": []}
