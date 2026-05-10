from typing import Protocol
import logging

class AgentEventWriter(Protocol):
    def on_thought(self, thought: str) -> None: ...
    def on_tool_start(self, tool_name: str) -> None: ...

class ConsoleEventWriter:
    def on_thought(self, thought: str) -> None:
        print(f"\n\033[96m🤔 [Agent Thoughts]:\033[0m \033[90m{thought}\033[0m")
        
    def on_tool_start(self, tool_name: str) -> None:
        print(f"\n\033[93m🛠️  [Running Tool]: {tool_name}\033[0m")

class LoggerEventWriter:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
    def on_thought(self, thought: str) -> None:
        self.logger.info(f"🤔 Agent Thoughts: {thought}")
        
    def on_tool_start(self, tool_name: str) -> None:
        self.logger.info(f"🛠️ Running Tool: {tool_name}")