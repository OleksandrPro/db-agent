import os
from dotenv import load_dotenv
from enum import Enum
from utils.logging import setup_logger


logger = setup_logger(__name__)

class EnvironmentType(str, Enum):
    TEST = "TEST"
    DEV = "DEV"
    PROD = "PROD"

load_dotenv()

class AppSettings: 
    _env_raw = os.getenv("ENVIRONMENT", "TEST").upper()
    
    try:
        ENVIRONMENT = EnvironmentType(_env_raw)
    except ValueError:
        logger.warning(f"Unknown ENVIRONMENT '{_env_raw}', falling back to DEV.")
        ENVIRONMENT = EnvironmentType.DEV
    
    MAX_ITERATIONS = 3

class DatabaseConfig:
    # Prod DB
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    
    PROD_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # Sandbox DB
    TEST_DB_USER = os.getenv("TEST_DB_USER")
    TEST_DB_PASSWORD = os.getenv("TEST_DB_PASSWORD")
    TEST_DB_NAME = os.getenv("TEST_DB_NAME")
    TEST_DB_PORT = os.getenv("TEST_DB_PORT")
    TEST_DB_HOST = os.getenv("TEST_DB_HOST")

    TEST_URL = f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"

class ApiKeys:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")