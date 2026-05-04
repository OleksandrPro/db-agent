from langchain_google_genai import ChatGoogleGenerativeAI
from ..protocol import ReviewStatus, CriticReview
from utils.logging import setup_logger


logger = setup_logger(__name__)

class GeminiCritic:
    def __init__(self, model_name: str, api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key
        ).with_structured_output(CriticReview)

    def review(self, user_prompt: str, original_schema: str, sandbox_schema: str, generated_sql: str) -> CriticReview:
        prompt = f"""
        You are a strict PostgreSQL Database Administrator and Code Reviewer.
        You must evaluate a proposed SQL migration based on TWO criteria:
        1. INTENT: Does the SQL strictly fulfill the USER REQUEST?
        2. SAFETY: Is the SQL perfectly safe to run on the ORIGINAL PRODUCTION SCHEMA containing gigabytes of existing data?

        [USER REQUEST]
        {user_prompt}
        
        [ORIGINAL PRODUCTION SCHEMA]
        {original_schema}
        
        [PROPOSED SQL MIGRATION]
        {generated_sql}
        
        [RESULTING SCHEMA (from Sandbox)]
        {sandbox_schema}
        
        EVALUATION LOGIC:
        - Step 1 (Intent): Check if the Resulting Schema matches what the user actually asked for. If it does not, return REJECTED_INTENT.
        - Step 2 (Safety): If intent is met, check for data loss, NOT NULL violations on existing rows, dropped columns in use, etc. If unsafe, return REJECTED_SAFETY.
        - Step 3 (Approve): If the query does exactly what the user wants AND is safe for existing data, return APPROVED.
        
        Provide specific, actionable feedback if rejected.
        """
        
        try:
            logger.debug(f"[Critic] Sending prompt to LLM:\n{prompt}")
            logger.info("Critic is evaluating Intent and Safety...")

            response: CriticReview = self.llm.invoke(prompt)

            logger.debug(f"[Critic] Structured Response: {response.model_dump()}")
            return response
        except Exception as e:
            logger.error(f"Critic failed to analyze: {e}")
            return CriticReview(
                status=ReviewStatus.REJECTED_SAFETY, 
                feedback=f"Critic System Error: {e}"
            )