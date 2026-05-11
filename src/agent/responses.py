from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from agent.status import NodeStatus


class GraphStateUpdate(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True, 
        validate_assignment=True, 
        arbitrary_types_allowed=True
    )

class ClassificationUpdate(GraphStateUpdate):
    status: Literal[NodeStatus.CLASSIFIER_PROCEED, NodeStatus.CLASSIFIER_OFF_TOPIC]
    classification_reasoning: str
    classification_message: Optional[str] = None

class IntrospectionUpdate(GraphStateUpdate):
    status: Optional[Literal[NodeStatus.SUCCESSFUL_EXTRACTION, NodeStatus.FAILED_EXTRACTION]] = None
    current_schema: Optional[str] = None
    error_log: Optional[str] = None
    logs: List[str]

class SQLGenerationUpdate(GraphStateUpdate):
    generated_sql: str
    iterations: int
    logs: List[str]

class TestSQLUpdate(GraphStateUpdate):
    status: Literal[
        NodeStatus.TEST_SUCCESS,
        NodeStatus.TEST_FAILED_SQL,
        NodeStatus.FATAL_SYSTEM_ERROR
    ]
    sandbox_schema: Optional[str] = None
    error_log: Optional[str] = None
    logs: List[str]

class CriticUpdate(GraphStateUpdate):
    status: Literal[
        NodeStatus.CRITIC_APPROVED,
        NodeStatus.CRITIC_REJECTED_INTENT,
        NodeStatus.CRITIC_REJECTED_SAFETY,
        NodeStatus.CRITIC_FAILED
    ]
    migration_summary: Optional[str] = None
    error_log: Optional[str] = None
    logs: List[str]

class HumanReviewUpdate(GraphStateUpdate):
    status: Literal[
        NodeStatus.HUMAN_APPROVED,
        NodeStatus.HUMAN_REJECTED_WITH_FEEDBACK,
        NodeStatus.HUMAN_ABORT
    ]
    human_feedback: Optional[str] = None
    error_log: Optional[str] = None
    logs: Optional[List[str]] = None
    iterations: Optional[int] = None

class DeployUpdate(GraphStateUpdate):
    status: Literal[
        NodeStatus.DEPLOY_SUCCESS,
        NodeStatus.DEPLOY_FAILED_DATA_CONFLICT,
        NodeStatus.DEPLOY_FAILED_FATAL
    ]
    error_log: Optional[str] = None
    logs: Optional[List[str]] = None

class HumanReviewPayload(BaseModel):
    sql: str = Field(description="The generated SQL migration.")
    original_schema: str = Field(description="The state of the database before migration.")
    sandbox_schema: str = Field(description="The state of the database after migration.")
    migration_summary: Optional[str] = Field(
        default=None, 
        description="Human-readable explanation of the changes (if approved) or the last critic feedback (in stalemate)."
    )
    iterations_spent: int = Field(description="Number of generation attempts used.")
    is_stalemate: bool = Field(description="True if the agent ran out of attempts.")

class HumanInterruptResponse(BaseModel):
    action: Literal["approve", "reject", "abort"] = Field(
        description="The decision made by the human reviewer."
    )
    feedback: Optional[str] = Field(
        default=None, 
        description="Text feedback provided if the action is 'reject'."
    )