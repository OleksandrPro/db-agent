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
def get_production_schema() -> ToolResult:
    """
    Use this tool FIRST to retrieve the current DDL schema of the production PostgreSQL database.
    
    WHEN TO USE:
    Always call this tool at the very beginning of the process.
    You must know the exact table structures, column names, and constraints to fulfill the user's request.
    
    Returns:
        A text string containing the complete SQL DDL representation of the current production database.
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
def reset_and_prepare_sandbox() -> ToolResult:
    """
    Use this tool to wipe the sandbox database clean and synchronize it with the current production schema.
    
    WHEN TO USE:
    You MUST call this tool BEFORE you attempt to execute any generated SQL in the sandbox.
    If your SQL fails and you generate a new one, you MUST call this tool again to reset the environment.
    
    Returns:
        A success message indicating the sandbox is ready for testing.
    """
    prod_engine = get_engine(settings.db_prod.url)
    test_engine = get_engine(settings.db_test.url)
    try:
        clone_schema(prod_engine, test_engine)
        msg = "SUCCESS: Sandbox database has been wiped and synchronized with production. Ready for testing."
        return ToolResult(outcome=ToolOutcome.SUCCESS, llm_message=msg)
    except SQLAlchemyError as e:
        return ToolResult(outcome=ToolOutcome.ERROR, llm_message=f"FATAL ERROR cloning schema: {str(e)}")
    finally:
        prod_engine.dispose()
        test_engine.dispose()

@tool
def execute_sandbox_sql(sql_query: str) -> ToolResult:
    """
    Use this tool to execute your generated SQL query in the isolated sandbox environment.
    
    WHEN TO USE:
    Call this ONLY AFTER you have successfully called `reset_and_prepare_sandbox`.
    
    Args:
        sql_query: The raw SQL string you want to test.
        
    Returns:
        If successful, returns a 'SUCCESS' message.
        If it fails, returns an 'ERROR' with PostgreSQL logs. You MUST generate new SQL and reset the sandbox if this happens.
    """
    test_engine = get_engine(settings.db_test.url)
    try:
        apply_sql_query(test_engine, sql_query)
        return ToolResult(
            outcome=ToolOutcome.SUCCESS, 
            llm_message="SUCCESS: Query executed successfully in the sandbox."
        )
    except SQLAlchemyError as e:
        return ToolResult(outcome=ToolOutcome.ERROR, llm_message=f"ERROR: {str(e)}")
    finally:
        test_engine.dispose()

@tool
def get_sandbox_schema() -> ToolResult:
    """
    Use this tool to retrieve the updated DDL schema from the sandbox AFTER you have executed your SQL.
    
    WHEN TO USE:
    Call this tool after `execute_sandbox_sql` returns SUCCESS. 
    Use this to visually verify that your SQL made the correct structural changes before asking the Critic for a review.
    
    Returns:
        A text string containing the DDL representation of the sandbox database.
    """
    test_engine = get_engine(settings.db_test.url)
    try:
        metadata = fetch_schema_metadata(test_engine)
        schema = metadata_to_ddl(test_engine, metadata)
        return ToolResult(outcome=ToolOutcome.SUCCESS, llm_message=schema, data=schema)
    except Exception as e:
        return ToolResult(outcome=ToolOutcome.ERROR, llm_message=f"Error extracting sandbox schema: {e}")
    finally:
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
    GET_PROD_SCHEMA = "get_production_schema"
    GENERATE_SQL = "generate_sql_migration"
    RESET_SANDBOX = "reset_and_prepare_sandbox"
    EXEC_SANDBOX = "execute_sandbox_sql"
    GET_SANDBOX_SCHEMA = "get_sandbox_schema"
    ASK_CRITIC = "ask_senior_dba_critic"
    DEPLOY = "execute_production_deployment"
