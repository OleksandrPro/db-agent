from sqlalchemy.exc import SQLAlchemyError
from config import DatabaseConfig
from agent.states import AgentState
from utils.db import (
    get_engine,
    fetch_schema_metadata,
    metadata_to_ddl,
    clone_schema,
    apply_sql_query
)
from agent.sql_generation.protocol import SQLGenerator
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
        return {"current_schema": full_schema, "logs": [msg]}
            
    except Exception as e:
        logger.error(f"Introspection failed: {e}")
        return {"status": "failed", "error_log": str(e), "logs": [f"Error: {e}"]}
    finally:
        engine.dispose()

def generate_sql_node(state: AgentState, generator: SQLGenerator):
    logger.info(f"Generating SQL for: {state['user_input']}")

    iterations = state.get("iterations", 0)
    error_log = state.get("error_log")

    retry_msg = f" (Retry {iterations})" if iterations > 0 else ""

    generated_sql = generator.generate(
        current_schema=state["current_schema"],
        user_input=state["user_input"],
        error_log=error_log
    )
    
    return {"generated_sql": generated_sql, "logs": [f"SQL Generated{retry_msg}."]}

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
            "status": "success", 
            "sandbox_schema": sandbox_schema, 
            "error_log": None, 
            "logs": [msg]
        }
    except SQLAlchemyError as e:
        err_msg = str(e)
        logger.warning(f"SQL Test failed: {err_msg}")
        return {
            "status": "failed_sql", 
            "error_log": err_msg,
            "iterations": state.get("iterations", 0) + 1,
            "logs": [f"Test failed: {err_msg}"]
        }
    except Exception as e:
        err_msg = f"System error during sandbox setup: {e}"
        logger.error(err_msg)
        return {
            "status": "fatal_system_error", 
            "error_log": err_msg, 
            "logs": [err_msg]
        }
    finally:
        prod_engine.dispose()
        test_engine.dispose()

def deploy_node(state: AgentState):
    logger.info("Deploying to production...")
    
    prod_engine = get_engine(DatabaseConfig.PROD_URL)
    try:
        apply_sql_query(prod_engine, state["generated_sql"])
        logger.info("Deployment simulated successfully.")
        return {"status": "deployed", "logs": ["Deployed to production."]}
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
            "status": "failed_sql_prod", 
            "error_log": extended_error_log,
            "iterations": state.get("iterations", 0) + 1,
            "logs": [f"Prod Data Error: {err_msg}"]
        }
    except Exception as e:
        logger.error(f"CRITICAL ERROR during deployment: {e}")
        return {"status": "failed_deploy", "error_log": str(e)}
    finally:
        prod_engine.dispose()
