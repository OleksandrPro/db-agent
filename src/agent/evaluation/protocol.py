from typing import Protocol
from enum import Enum
from pydantic import BaseModel, Field

class ReviewStatus(str, Enum):
    APPROVED = "approved"
    REJECTED_INTENT = "rejected_intent"
    REJECTED_SAFETY = "rejected_safety"

class CriticReview(BaseModel):
    status: ReviewStatus = Field(
        description="The final verdict of the review. Choose APPROVED only if BOTH intent is met and it is completely safe."
    )
    feedback: str = Field(
        description="Detailed, actionable feedback. If REJECTED_INTENT, explain what is missing from the user's prompt. If REJECTED_SAFETY, explain how to fix the SQL to make it safe."
    )

class SQLReviewer(Protocol):
    def review(self, user_prompt: str, original_schema: str, sandbox_schema: str, generated_sql: str) -> CriticReview:
        ...