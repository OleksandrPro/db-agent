from langchain_google_genai import ChatGoogleGenerativeAI
from config import ApiKeys
from ..protocol import SQLGenerator

class GeminiSQLGenerator:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=ApiKeys.GOOGLE_API_KEY
        )

    def generate(self, current_schema: str, user_input: str) -> str:
        system_prompt = (
            "You are a Senior PostgreSQL Architect. "
            "Output ONLY raw SQL without explanations."
        )
        user_content = f"SCHEMA:\n{current_schema}\n\nREQUEST: {user_input}"
        
        response = self.llm.invoke([
            ("system", system_prompt),
            ("user", user_content)
        ])
        return response.content.strip()
