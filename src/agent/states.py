from typing import TypedDict, Optional, Annotated, List
import operator

class AgentState(TypedDict):
    user_input: str
    current_schema: Optional[str]
    generated_sql: Optional[str]
    error_log: Optional[str]
    iterations: int
    status: str
    logs: Annotated[List[str], operator.add]