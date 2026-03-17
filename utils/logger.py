from loguru import logger
import sys

# Logger config
logger.remove()

logger.add(sys.stdout, format="{message}", level="INFO")
