from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal, Any
from agent.status import NodeStatus, ToolOutcome


class GraphStateUpdate(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True, 
        validate_assignment=True, 
        arbitrary_types_allowed=True
    )

class ClassificationUpdate(GraphStateUpdate):
    messages: List[Any] = Field(default_factory=list)
    status: Literal[NodeStatus.CLASSIFIER_PROCEED, NodeStatus.CLASSIFIER_OFF_TOPIC]
    classification_reasoning: str
    classification_message: Optional[str] = None

class AgentUpdate(GraphStateUpdate):
    messages: List[Any]

class ExecuteToolsUpdate(GraphStateUpdate):
    messages: List[Any]
    generated_sql: Optional[str] = None
    iterations: Optional[int] = None
    current_schema: Optional[str] = None
    sandbox_schema: Optional[str] = None
    status: Optional[str] = None
    migration_summary: Optional[str] = None

class HumanReviewUpdate(GraphStateUpdate):
    messages: List[Any] = Field(default_factory=list)
    status: Literal[
        NodeStatus.HUMAN_APPROVED,
        NodeStatus.HUMAN_REJECTED_WITH_FEEDBACK,
        NodeStatus.HUMAN_ABORT
    ]
    human_feedback: Optional[str] = None
    error_log: Optional[str] = None
    logs: Optional[List[str]] = None
    iterations: Optional[int] = None

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

class ToolResult(BaseModel):
    outcome: ToolOutcome
    llm_message: str
    data: Optional[Any] = None