from typing import Protocol

class SQLGenerator(Protocol):
    def generate(self, current_schema: str, user_input: str, error_log: str | None = None) -> str:
        ...