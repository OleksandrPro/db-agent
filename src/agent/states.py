from typing import TypedDict, Optional

class AgentState(TypedDict):
    user_input: str
    current_schema: Optional[str]
    generated_sql: Optional[str]
    error_log: Optional[str]
    iterations: int
    status: str