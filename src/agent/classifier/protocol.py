from enum import Enum
from pydantic import BaseModel, Field
from typing import Protocol

class ClassificationStatus(str, Enum):
    PROCEED = "proceed"
    OFF_TOPIC = "off_topic"

class ClassificationResult(BaseModel):
    status: ClassificationStatus = Field(description="Decision whether to process the prompt or not")
    reasoning: str = Field(description="Short explanation of why this decision was made")
    message: str | None = Field(None, description="Polite message for the user if the status is OFF_TOPIC")

class PromptClassifier(Protocol):
    def classify(self, user_input: str) -> ClassificationResult:
        ...