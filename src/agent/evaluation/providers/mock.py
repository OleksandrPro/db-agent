from ..protocol import ReviewStatus, CriticReview
from utils.logging import setup_logger


logger = setup_logger(__name__)

class MockCritic:
    def __init__(self):
        self._call_count = 0
        
    def review(self, user_prompt: str, original_schema: str, sandbox_schema: str, generated_sql: str) -> CriticReview:
        self._call_count += 1
        
        if self._call_count == 1:
            logger.warning("[Mock Critic] Intent check failed!")
            return CriticReview(
                status=ReviewStatus.REJECTED_INTENT,
                feedback="You added a 'test_column', but the user asked to add 'last_login'. Please fix the column name."
            )
            
        elif self._call_count == 2:
            logger.warning("[Mock Critic] Safety check failed!")
            return CriticReview(
                status=ReviewStatus.REJECTED_SAFETY,
                feedback="You are adding 'last_login' as NOT NULL, but didn't provide a DEFAULT. This will crash on existing production data."
            )
            
        logger.info("[Mock Critic] Intent and Safety both passed.")
        return CriticReview(status=ReviewStatus.APPROVED, feedback="Approved.")