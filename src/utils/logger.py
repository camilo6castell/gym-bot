import sys

from loguru import logger

# Logger config
logger.remove()

# logger.add(sys.stdout, format="{message}", level="INFO")

logger.add(
    sys.stdout,
    # Level minimum to log
    level="INFO",
    format=(
        # "{time:YYYY-MM-DD HH:mm:ss}"
        "<green>{time:MM/DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "{message}"
    ),
)

# Example log message:
# 07/09 20:41:31 | INFO     | src.components.login:perform_login:7 | Logging into SmartFit
