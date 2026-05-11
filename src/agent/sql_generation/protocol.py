from typing import Protocol
from pydantic import BaseModel, Field

class GeneratedSQL(BaseModel):
    query: str = Field(description="The raw PostgreSQL query without any markdown or explanations.")

class SQLGenerator(Protocol):
    def generate(self, current_schema: str, user_input: str, error_log: str | None = None) -> GeneratedSQL:
        ...