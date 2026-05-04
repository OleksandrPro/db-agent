from config import settings, EnvironmentType
from agent.sql_generation.protocol import SQLGenerator
from agent.sql_generation.providers import MockSQLGenerator, GeminiSQLGenerator
from agent.evaluation.protocol import SQLReviewer
from agent.evaluation.providers.mock import MockCritic
from agent.evaluation.providers.gemini import GeminiCritic
from utils.logging import setup_logger


logger = setup_logger(__name__)

def get_sql_generation_llm() -> SQLGenerator:
    env = settings.environment
    
    match env:
        case EnvironmentType.DEV:
            logger.info("Environment is DEV. Using MockSQLGenerator.")
            return MockSQLGenerator()
        
        case EnvironmentType.TEST:
            logger.info("Environment is TEST. Using GeminiSQLGenerator.")
            return GeminiSQLGenerator(
                model_name=settings.models.generator, 
                api_key=settings.google_api_key
            )
        
        case EnvironmentType.PROD:
            logger.info("Environment is PROD. Using GeminiSQLGenerator.")
            return GeminiSQLGenerator(
                model_name=settings.models.generator, 
                api_key=settings.google_api_key
            )

def get_critic_llm() -> SQLReviewer:
    env = settings.environment
    
    match env:
        case EnvironmentType.DEV:
            logger.info("Environment is DEV. Using MockCritic.")
            return MockCritic()
        case EnvironmentType.TEST:
            logger.info("Environment is TEST. Using GeminiCritic.")
            return GeminiCritic(
                model_name=settings.models.critic, 
                api_key=settings.google_api_key
            )
        case EnvironmentType.PROD:
            logger.info("Environment is PROD. Using GeminiCritic.")
            return GeminiCritic(
                model_name=settings.models.critic, 
                api_key=settings.google_api_key
            )
