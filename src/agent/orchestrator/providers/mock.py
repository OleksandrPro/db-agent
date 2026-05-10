from typing import Any, List
from langchain_core.messages import AIMessage, BaseMessage

class MockOrchestratorLLM:
    def bind_tools(self, tools: list[Any]) -> 'MockOrchestratorLLM':
        return self

    def invoke(self, messages: List[BaseMessage]) -> BaseMessage:
        return AIMessage(content="[MOCK AGENT] I am pretending to think. No tools called.")