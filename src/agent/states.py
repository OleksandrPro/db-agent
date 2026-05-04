from typing import TypedDict, Optional, Annotated, List
import operator

class AgentState(TypedDict):
    user_input: str

    classification_reasoning: Optional[str]
    classification_message: Optional[str]

    current_schema: Optional[str]
    generated_sql: Optional[str]
    sandbox_schema: Optional[str]
    error_log: Optional[str]
    iterations: int
    status: str
    logs: Annotated[List[str], operator.add]