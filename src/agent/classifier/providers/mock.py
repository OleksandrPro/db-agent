from ..protocol import ClassificationResult, ClassificationStatus
from utils.logging import setup_logger

logger = setup_logger(__name__)

class MockClassifier:
    def classify(self, user_input: str) -> ClassificationResult:
        logger.info("[Mock Classifier] Simulating classification...")
        
        keywords = ["table", "column", "add", "drop", "index", "database", "sql", "users", "orders"]
        is_db_task = any(word in user_input.lower() for word in keywords)
        
        if is_db_task:
            return ClassificationResult(
                status=ClassificationStatus.PROCEED,
                reasoning="Input contains database-related keywords."
            )
        
        return ClassificationResult(
            status=ClassificationStatus.OFF_TOPIC,
            reasoning="No database keywords found.",
            message="I'm a DB Migration Agent. I can only help you with database schema changes."
        )