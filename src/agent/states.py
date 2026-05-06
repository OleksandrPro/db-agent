from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Annotated, List, Literal
from agent.status import NodeStatus

def add_logs(left: List[str], right: List[str]) -> List[str]:
    return (left or []) + (right or [])

class AgentState(BaseModel):
    user_input: str

    classification_reasoning: Optional[str] = None
    classification_message: Optional[str] = None

    current_schema: Optional[str] = None
    generated_sql: Optional[str] = None
    sandbox_schema: Optional[str] = None
    error_log: Optional[str] = None
    iterations: int = 0
    status: NodeStatus | Literal["pending"] = "pending"
    logs: Annotated[List[str], add_logs] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True)