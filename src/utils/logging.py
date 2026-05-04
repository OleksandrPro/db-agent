import logging
import sys
from config import settings, EnvironmentType

def setup_logger(name: str):
    logger = logging.getLogger(name)
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%d-%m-%Y %H:%M:%S'
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        if settings.environment == EnvironmentType.PROD:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.DEBUG)
    return logger