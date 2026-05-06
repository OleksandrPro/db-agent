from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from agent.status import NodeStatus


class ClassificationUpdate(BaseModel):
    status: Literal[NodeStatus.CLASSIFIER_PROCEED, NodeStatus.CLASSIFIER_OFF_TOPIC]
    classification_reasoning: str
    classification_message: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)

class IntrospectionUpdate(BaseModel):
    status: Optional[Literal[NodeStatus.SUCCESSFUL_EXTRACTION, NodeStatus.FAILED_EXTRACTION]] = None
    current_schema: Optional[str] = None
    error_log: Optional[str] = None
    logs: List[str]

    model_config = ConfigDict(use_enum_values=True)

class SQLGenerationUpdate(BaseModel):
    generated_sql: str
    iterations: int
    logs: List[str]

    model_config = ConfigDict(use_enum_values=True)

class TestSQLUpdate(BaseModel):
    status: Literal[
        NodeStatus.TEST_SUCCESS,
        NodeStatus.TEST_FAILED_SQL,
        NodeStatus.FATAL_SYSTEM_ERROR
    ]
    sandbox_schema: Optional[str] = None
    error_log: Optional[str] = None
    logs: List[str]

    model_config = ConfigDict(use_enum_values=True)

class CriticUpdate(BaseModel):
    status: Literal[
        NodeStatus.CRITIC_APPROVED,
        NodeStatus.CRITIC_REJECTED_INTENT,
        NodeStatus.CRITIC_REJECTED_SAFETY,
        NodeStatus.CRITIC_FAILED
    ]
    error_log: Optional[str] = None
    logs: List[str]

    model_config = ConfigDict(use_enum_values=True)

class HumanReviewUpdate(BaseModel):
    status: Literal[
        NodeStatus.HUMAN_APPROVED,
        NodeStatus.HUMAN_REJECTED_WITH_FEEDBACK,
        NodeStatus.HUMAN_ABORT
    ]
    human_feedback: Optional[str] = None
    error_log: Optional[str] = None
    logs: Optional[List[str]] = None
    iterations: Optional[int] = None

    model_config = ConfigDict(use_enum_values=True)

class DeployUpdate(BaseModel):
    status: Literal[
        NodeStatus.DEPLOY_SUCCESS,
        NodeStatus.DEPLOY_FAILED_DATA_CONFLICT,
        NodeStatus.DEPLOY_FAILED_FATAL
    ]
    error_log: Optional[str] = None
    logs: Optional[List[str]] = None

    model_config = ConfigDict(use_enum_values=True)

class HumanInterruptResponse(BaseModel):
    action: Literal["approve", "reject", "abort"] = Field(
        description="The decision made by the human reviewer."
    )
    feedback: Optional[str] = Field(
        default=None, 
        description="Text feedback provided if the action is 'reject'."
    )