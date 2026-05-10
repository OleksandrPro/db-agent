from config import settings, EnvironmentType
from agent.classifier.protocol import PromptClassifier
from agent.classifier.providers import MockClassifier, GeminiClassifier
from agent.sql_generation.protocol import SQLGenerator
from agent.sql_generation.providers import MockSQLGenerator, GeminiSQLGenerator
from agent.evaluation.protocol import SQLReviewer
from agent.evaluation.providers import MockCritic, GeminiCritic
from agent.orchestrator.protocol import OrchestratorLLM
from agent.orchestrator.providers import MockOrchestratorLLM, get_gemini_orchestrator
from utils.logging import setup_logger


logger = setup_logger(__name__)

def get_classifier_llm() -> PromptClassifier:
    match settings.environment:
        case EnvironmentType.DEV:
            return MockClassifier()
        
        case EnvironmentType.TEST | EnvironmentType.PROD:
            return GeminiClassifier(
                model_name=settings.models.classifier, 
                api_key=settings.google_api_key.get_secret_value()
            )

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
                api_key=settings.google_api_key.get_secret_value()
            )
        
        case EnvironmentType.PROD:
            logger.info("Environment is PROD. Using GeminiSQLGenerator.")
            return GeminiSQLGenerator(
                model_name=settings.models.generator, 
                api_key=settings.google_api_key.get_secret_value()
            )

def get_critic_llm() -> SQLReviewer:
    env = settings.environment
    
    match settings.environment:
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

def get_agent_llm() -> OrchestratorLLM:
    env = settings.environment
    
    match env:
        case EnvironmentType.DEV:
            logger.info("Environment is DEV. Using MockOrchestratorLLM.")
            return MockOrchestratorLLM()
        case EnvironmentType.TEST:
            logger.info("Environment is TEST. Using Gemini Orchestrator.")
            return get_gemini_orchestrator(
                model_name=settings.models.agent, 
                api_key=settings.google_api_key.get_secret_value()
            )
        case EnvironmentType.PROD:
            logger.info("Environment is PROD. Using Gemini Orchestrator.")
            return get_gemini_orchestrator(
                model_name=settings.models.agent, 
                api_key=settings.google_api_key.get_secret_value()
            )
