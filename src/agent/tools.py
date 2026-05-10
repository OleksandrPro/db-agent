from enum import Enum
from langchain_core.tools import tool
from sqlalchemy.exc import SQLAlchemyError
from utils.db import get_engine, clone_schema, apply_sql_query, fetch_schema_metadata, metadata_to_ddl
from agent.sql_generation.protocol import SQLGenerator
from agent.evaluation.protocol import SQLReviewer
from agent.responses import ToolResult
from agent.status import ToolOutcome
from config import settings


@tool
def get_database_schema() -> ToolResult:
    """
    Use this tool FIRST to retrieve the current DDL schema of the production PostgreSQL database.
    
    WHEN TO USE:
    Always call this tool at the very beginning of the process before attempting to generate any SQL.
    You must know the exact table structures, column names, and constraints to fulfill the user's request.
    
    Returns:
        A text string containing the complete SQL DDL representation of the current database schema.
    """
    engine = get_engine(settings.db_prod.url)
    try:
        metadata = fetch_schema_metadata(engine)
        schema = metadata_to_ddl(engine, metadata)
        return ToolResult(outcome=ToolOutcome.SUCCESS, llm_message=schema, data=schema)
    except Exception as e:
        return ToolResult(outcome=ToolOutcome.FATAL, llm_message=f"Error extracting schema: {e}")
    finally:
        engine.dispose()

def make_sql_generation_tool(generator: SQLGenerator):
    @tool
    def generate_sql_migration(user_request: str, database_schema: str, error_log: str = None) -> ToolResult:
        """
        Use this tool to generate the raw SQL migration query based on the user's request.
        
        WHEN TO USE:
        Call this tool after you have successfully retrieved the database schema. 
        You must also call this tool again if your previous SQL failed the sandbox test or was rejected by the Critic.
        
        Args:
            user_request: The original instruction provided by the user.
            database_schema: The current DDL schema obtained from get_database_schema.
            error_log: Provide the error message here if you are retrying a failed query. Leave as None for the first attempt.
            
        Returns:
            A text string containing ONLY the generated raw SQL query.
        """
        sql = generator.generate(
            current_schema=database_schema,
            user_input=user_request,
            error_log=error_log
        )
        return ToolResult(outcome=ToolOutcome.SUCCESS, llm_message=sql, data=sql)
    return generate_sql_migration

@tool
def test_sql_in_sandbox(sql_query: str) -> ToolResult:
    """
    Use this tool to safely execute and validate your generated SQL migration query in an isolated sandbox environment.
    
    WHEN TO USE:
    Call this tool IMMEDIATELY after generating an SQL query. NEVER skip this step. 
    Do not ask the Critic for review until this tool returns a SUCCESS message.
    
    Args:
        sql_query: The raw SQL string you want to test.
        
    Returns:
        If successful, returns a string starting with 'SUCCESS' followed by the new database schema.
        If it fails, returns a string starting with 'ERROR' followed by detailed PostgreSQL error logs. 
        If you receive an ERROR, you MUST use generate_sql_migration again and pass this error log.
    """
    prod_engine = get_engine(settings.db_prod.url)
    test_engine = get_engine(settings.db_test.url)
    try:
        clone_schema(prod_engine, test_engine)
        apply_sql_query(test_engine, sql_query)
        metadata = fetch_schema_metadata(test_engine)
        schema = metadata_to_ddl(test_engine, metadata)
        
        return ToolResult(
            outcome=ToolOutcome.SUCCESS, 
            llm_message=f"SUCCESS. Resulting Schema:\n{schema}", 
            data=schema
        )
    except SQLAlchemyError as e:
        return ToolResult(outcome=ToolOutcome.ERROR, llm_message=f"ERROR: {str(e)}")
    finally:
        prod_engine.dispose()
        test_engine.dispose()

def make_critic_tool(critic: SQLReviewer):
    @tool
    def ask_senior_dba_critic(original_schema: str, sandbox_schema: str, proposed_sql: str, user_request: str) -> ToolResult:
        """
        Use this tool to request a mandatory peer review from a Senior Database Administrator (Critic).
        
        WHEN TO USE:
        Call this tool ONLY AFTER the SQL has successfully passed the test_sql_in_sandbox tool.
        The Critic will evaluate the SQL for structural safety (preventing data loss) and intent accuracy.
        
        Args:
            original_schema: The original DB schema before any changes.
            sandbox_schema: The resulting schema returned by the successful sandbox test.
            proposed_sql: The exact SQL query that passed the sandbox test.
            user_request: The original request from the user.
            
        Returns:
            A review text string. 
            If APPROVED, it includes a human-readable summary of the changes. You are now ready to stop and await human approval.
            If REJECTED, it includes detailed feedback. You MUST use generate_sql_migration again to fix the issues mentioned in the feedback.
        """
        review = critic.review(
            user_prompt=user_request, original_schema=original_schema, 
            sandbox_schema=sandbox_schema, generated_sql=proposed_sql
        )
        if review.status == "approved":
            summary = review.summary or review.feedback
            return ToolResult(
                outcome=ToolOutcome.SUCCESS, 
                llm_message=f"APPROVED. Summary: {summary}",
                data=summary
            )
        return ToolResult(outcome=ToolOutcome.ERROR, llm_message=f"REJECTED. Feedback: {review.feedback}")
    return ask_senior_dba_critic

@tool
def execute_production_deployment(sql_query: str) -> ToolResult:
    """
    Use this tool to apply the final, approved SQL migration directly to the production database.
    
    WHEN TO USE:
    Call this tool ONLY AFTER you have received explicit approval from the Human user. 
    Never call this tool autonomously based only on the Critic's approval.
    
    Args:
        sql_query: The strictly tested and approved SQL query.
        
    Returns:
        A text string containing a success or failure message regarding the production deployment.
    """
    engine = get_engine(settings.db_prod.url)
    try:
        apply_sql_query(engine, sql_query)
        return ToolResult(outcome=ToolOutcome.SUCCESS, llm_message="SUCCESS: Migration applied to production.")
    except SQLAlchemyError as e:
        msg = f"DATA_CONFLICT: FAILED during Production deployment. Error: {str(e)}."
        return ToolResult(outcome=ToolOutcome.DATA_CONFLICT, llm_message=msg)
    except Exception as e:
        return ToolResult(outcome=ToolOutcome.FATAL, llm_message=f"FATAL_ERROR: Critical system error: {str(e)}")
    finally:
        engine.dispose()

class ToolName(str, Enum):
    GET_SCHEMA = "get_database_schema"
    GENERATE_SQL = "generate_sql_migration"
    TEST_SQL = "test_sql_in_sandbox"
    ASK_CRITIC = "ask_senior_dba_critic"
    DEPLOY = "execute_production_deployment"
