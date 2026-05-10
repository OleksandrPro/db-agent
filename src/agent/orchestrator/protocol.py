from typing import Protocol, Any, List
from langchain_core.messages import BaseMessage

class OrchestratorLLM(Protocol):
    def bind_tools(self, tools: list[Any]) -> 'OrchestratorLLM':
        ...

    def invoke(self, messages: List[BaseMessage]) -> BaseMessage:
        ...