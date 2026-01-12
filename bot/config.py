import os
from dotenv import load_dotenv

load_dotenv()


def env_bool(name: str, default=False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")


BOT_HEADLESS = env_bool("BOT_HEADLESS", True)
# BOT_ENV = os.getenv("BOT_ENV", "prod")

BOT_FORCE_RUN = env_bool("BOT_FORCE_RUN", False)
BOT_FORCE_RUN_CLASS = os.getenv("BOT_FORCE_RUN_CLASS")
BOT_FORCE_RUN_HOUR = os.getenv("BOT_FORCE_RUN_HOUR")
BOT_FORCE_RUN_DAY = os.getenv("BOT_FORCE_RUN_DAY")
