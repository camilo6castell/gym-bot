from typing import cast

import requests

from src.notifications import Notifier, TelegramUpdatesResponse
from src.utils.logger import logger


class TelegramClient(Notifier):
    """
    Encapsulates interactions with the Telegram Bot API.

    The client uses a bot token and chat ID to send messages and retrieve
    updates.  All network calls are wrapped in try/except blocks that
    log failures via `logger`.
    """

    def __init__(self, token: str, chat_id: str) -> None:
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
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": self._chat_id, "text": msg},
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Telegram notify failed: {e}", exc_info=True)

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
            response = requests.get(f"{self.base_url}/getUpdates", timeout=10)
            response.raise_for_status()
            return cast(TelegramUpdatesResponse, response.json())
        except requests.RequestException as e:
            logger.error(f"Telegram get_updates failed: {e}", exc_info=True)
            return {"result": []}

