from langchain_google_genai import ChatGoogleGenerativeAI
from ..protocol import SQLGenerator

class GeminiSQLGenerator:
    def __init__(self, model_name: str, api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key
        )

    def generate(self, current_schema: str, user_input: str, error_log: str | None = None) -> str:
        prompt = f"""
            "You are a Senior PostgreSQL Architect. "
                Current schema:
            {current_schema}
            
            Task: {user_input}
            
            Return ONLY valid SQL. No markdown, no explanations.
            """

        if error_log:
            prompt += f"\n\nCRITICAL FIX REQUIRED:\nYour previous SQL query failed with the following error:\n{error_log}\n\nPlease analyze the error and provide a corrected SQL query."

        response = self.llm.invoke(prompt)


        sql = response.content.strip()
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.endswith("```"):
            sql = sql[:-3]
            
        return sql.strip()
