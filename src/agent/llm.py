from config import AppSettings, EnvironmentType
from agent.sql_generation.protocol import SQLGenerator
from agent.sql_generation.providers import MockSQLGenerator, GeminiSQLGenerator
from utils.logging import setup_logger


logger = setup_logger(__name__)

def get_sql_generation_llm() -> SQLGenerator:
    env = AppSettings.ENVIRONMENT
    
    match env:
        case EnvironmentType.DEV:
            logger.info("Environment is DEV. Using MockSQLGenerator.")
            return MockSQLGenerator()
        
        case EnvironmentType.TEST:
            logger.info("Environment is TEST. Using GeminiSQLGenerator.")
            return GeminiSQLGenerator()
        
        case EnvironmentType.PROD:
            logger.info("Environment is PROD. Using GeminiSQLGenerator.")
            return GeminiSQLGenerator()
