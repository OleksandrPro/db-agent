from sqlalchemy.exc import SQLAlchemyError
from config import DatabaseConfig
from agent.states import AgentState
from agent.status import NodeStatus
from utils.db import (
    get_engine,
    fetch_schema_metadata,
    metadata_to_ddl,
    clone_schema,
    apply_sql_query
)
from agent.sql_generation.protocol import SQLGenerator
from agent.evaluation.protocol import SQLReviewer, ReviewStatus
from utils.logging import setup_logger


logger = setup_logger(__name__)

def introspect_db_node(state: AgentState):
    logger.info("Starting introspection...")
    
    engine = get_engine(DatabaseConfig.PROD_URL)

    try:
        metadata = fetch_schema_metadata(engine)
        full_schema = metadata_to_ddl(engine, metadata)
        
        msg = f"Reflected {len(metadata.tables)} tables."
        logger.info(msg)
        return {
            "current_schema": full_schema,
            "logs": [msg]
        }
            
    except Exception as e:
        logger.error(f"Introspection failed: {e}")
        return {
            "status": NodeStatus.FAILED_EXTRACTION,
            "error_log": str(e),
            "logs": [f"Error: {e}"]
        }
    finally:
        engine.dispose()

def generate_sql_node(state: AgentState, generator: SQLGenerator):
    current_iteration = state.get("iterations", 0) + 1

    logger.info(f"Generating SQL for: {state['user_input']}")

    iterations = state.get("iterations", 0)
    error_log = state.get("error_log")

    retry_msg = f" (Retry {iterations})" if iterations > 0 else ""

    generated_sql = generator.generate(
        current_schema=state["current_schema"],
        user_input=state["user_input"],
        error_log=error_log
    )
    
    return {
        "generated_sql": generated_sql,
        "iterations": current_iteration,
        "logs": [f"SQL Generated{retry_msg}."]
    }

def test_sql_node(state: AgentState):
    logger.info("Testing SQL in sandbox...")
    
    prod_engine = get_engine(DatabaseConfig.PROD_URL)
    test_engine = get_engine(DatabaseConfig.TEST_URL)
    
    try:
        clone_schema(prod_engine, test_engine)
        
        generated_sql = state["generated_sql"]
        apply_sql_query(test_engine, generated_sql)

        sandbox_metadata = fetch_schema_metadata(test_engine)
        sandbox_schema = metadata_to_ddl(test_engine, sandbox_metadata)
        
        msg = "Sandbox test passed."
        logger.info(msg)
        return {
            "status": NodeStatus.TEST_SUCCESS, 
            "sandbox_schema": sandbox_schema, 
            "error_log": None, 
            "logs": [msg]
        }
    except SQLAlchemyError as e:
        err_msg = str(e)
        logger.warning(f"SQL Test failed: {err_msg}")
        return {
            "status": NodeStatus.TEST_FAILED_SQL, 
            "error_log": err_msg,
            "logs": [f"Test failed: {err_msg}"]
        }
    except Exception as e:
        err_msg = f"System error during sandbox setup: {e}"
        logger.error(err_msg)
        return {
            "status": NodeStatus.FATAL_SYSTEM_ERROR, 
            "error_log": err_msg, 
            "logs": [err_msg]
        }
    finally:
        prod_engine.dispose()
        test_engine.dispose()

def critic_node(state: AgentState, critic: SQLReviewer):
    logger.info("Critic is reviewing the migration...")
    
    review_result = critic.review(
        user_prompt=state["user_input"],
        original_schema=state["current_schema"],
        sandbox_schema=state["sandbox_schema"],
        generated_sql=state["generated_sql"]
    )
    
    if review_result.status == ReviewStatus.APPROVED:
        msg = "Critic approved the migration. It is safe and accurate."
        logger.info(msg)
        return {
            "status": NodeStatus.CRITIC_APPROVED,
            "error_log": None,
            "logs": [msg]
        }
        
    elif review_result.status == ReviewStatus.REJECTED_INTENT:
        err_msg = f"CRITIC REJECTED (Intent mismatch): {review_result.feedback}"
        logger.warning(err_msg)
        return {
            "status": NodeStatus.CRITIC_REJECTED_INTENT,
            "error_log": err_msg,
            "logs": [err_msg]
        }
        
    elif review_result.status == ReviewStatus.REJECTED_SAFETY:
        err_msg = f"CRITIC REJECTED (Safety hazard): {review_result.feedback}"
        logger.warning(err_msg)
        return {
            "status": NodeStatus.CRITIC_REJECTED_SAFETY,
            "error_log": err_msg,
            "logs": [err_msg]
        }
    else:
        err_msg = f"Critic failed to provide a valid review: {review_result.feedback}"
        logger.error(err_msg)
        return {"status": NodeStatus.CRITIC_FAILED, "error_log": err_msg, "logs": [err_msg]}

def deploy_node(state: AgentState):
    logger.info("Deploying to production...")
    
    prod_engine = get_engine(DatabaseConfig.PROD_URL)
    try:
        apply_sql_query(prod_engine, state["generated_sql"])
        logger.info("Deployment simulated successfully.")
        return {"status": NodeStatus.DEPLOY_SUCCESS, "logs": ["Deployed to production."]}
    except SQLAlchemyError as e:
        # Error while applying sql-query to the prod db
        err_msg = str(e)
        logger.error(f"CRITICAL SQL DATA ERROR during deployment: {err_msg}")

        extended_error_log = (
            f"SYNTAX OK, BUT DATA CONFLICT: Your query successfully passed the Sandbox test "
            f"(the syntax and schema are correct), but FAILED during Production deployment "
            f"due to existing data. Production Error: {err_msg}. "
            f"Please adjust the query to handle existing rows safely."
        )

        return {
            "status": NodeStatus.DEPLOY_FAILED_DATA_CONFLICT, 
            "error_log": extended_error_log,
            "logs": [f"Prod Data Error: {err_msg}"]
        }
    except Exception as e:
        logger.error(f"CRITICAL ERROR during deployment: {e}")

        return {
            "status": NodeStatus.DEPLOY_FAILED_FATAL,
            "error_log": str(e)
        }
    finally:
        prod_engine.dispose()
