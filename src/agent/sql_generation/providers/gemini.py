from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from ..protocol import SQLGenerator, GeneratedSQL
from utils.logging import setup_logger


logger = setup_logger(__name__)

class GeminiSQLGenerator:
    def __init__(self, model_name: str, api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.1
        ).with_structured_output(GeneratedSQL)

    def generate(self, current_schema: str, user_input: str, error_log: str | None = None) -> str:
        system_prompt = (
            "You are a Senior PostgreSQL Architect.\n"
            "Write valid SQL to fulfill the user's request based on the schema.\n"
            "Return ONLY valid SQL. No markdown, no explanations."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Current schema:\n{current_schema}\n\nTask: {user_input}")
        ]
        
        if error_log:
            error_msg = f"CRITICAL FIX REQUIRED:\nYour previous SQL query failed with error:\n{error_log}\nFix the SQL."
            messages.append(HumanMessage(content=error_msg))

        logger.info("Generating SQL...")

        response: GeneratedSQL = self.llm.invoke(messages)

        logger.debug(f"[SQL Generator] Structured LLM Response:\n{response.query}")
        
        return response.query
