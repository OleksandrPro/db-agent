from config import AppSettings, EnvironmentType, Models, ApiKeys
from agent.sql_generation.protocol import SQLGenerator
from agent.sql_generation.providers import MockSQLGenerator, GeminiSQLGenerator
from agent.evaluation.protocol import SQLReviewer
from agent.evaluation.providers.mock import MockCritic
from agent.evaluation.providers.gemini import GeminiCritic
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
            return GeminiSQLGenerator(
                model_name=Models.GENERATOR_LLM_MODEL, 
                api_key=ApiKeys.GOOGLE_API_KEY
            )
        
        case EnvironmentType.PROD:
            logger.info("Environment is PROD. Using GeminiSQLGenerator.")
            return GeminiSQLGenerator(
                model_name=Models.GENERATOR_LLM_MODEL, 
                api_key=ApiKeys.GOOGLE_API_KEY
            )

def get_critic_llm() -> SQLReviewer:
    env = AppSettings.ENVIRONMENT
    
    match env:
        case EnvironmentType.DEV:
            logger.info("Environment is DEV. Using MockCritic.")
            return MockCritic()
        case EnvironmentType.TEST:
            logger.info("Environment is TEST. Using GeminiCritic.")
            return GeminiCritic(
                model_name=Models.CRITIC_LLM_MODEL, 
                api_key=ApiKeys.GOOGLE_API_KEY
            )
        case EnvironmentType.PROD:
            logger.info("Environment is PROD. Using GeminiCritic.")
            return GeminiCritic(
                model_name=Models.CRITIC_LLM_MODEL, 
                api_key=ApiKeys.GOOGLE_API_KEY
            )
