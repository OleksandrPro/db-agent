from typing import Literal
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

    retry_msg = f" (Retry {state['iterations']})" if state.get("iterations", 0) > 0 else ""

    generated_sql = generator.generate(
        current_schema=state["current_schema"],
        user_input=state["user_input"]
    )
    
    return {"generated_sql": generated_sql, "logs": [f"SQL Generated{retry_msg}."]}

def test_sql_node(state: AgentState):
    logger.info("Testing SQL in sandbox...")
    
    prod_engine = get_engine(DatabaseConfig.PROD_URL)
    test_engine = get_engine(DatabaseConfig.TEST_URL)
    
    try:
        clone_schema(prod_engine, test_engine)
        
        generated_sql = state["generated_sql"]
        print(f"Executing: {generated_sql}")
        apply_sql_query(test_engine, generated_sql)
        
        msg = "Sandbox test passed."
        logger.info(msg)
        return {"status": "success", "error_log": None, "logs": [msg]}
    except Exception as e:
        err_msg = str(e)
        logger.warning(f"Test failed: {err_msg}")
        return {
            "status": "failed", 
            "error_log": err_msg,
            "iterations": state.get("iterations", 0) + 1,
            "logs": [f"Test failed: {err_msg}"]
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
    except Exception as e:
        logger.error(f"CRITICAL ERROR during deployment: {e}")
        return {"status": "failed_deploy", "error_log": str(e)}
    finally:
        prod_engine.dispose()

def should_continue(state: AgentState) -> Literal["deploy", "generate", "end"]:
    if state["status"] == "success":
        return "deploy"
    if state["iterations"] < 3:
        return "generate"
    return "end"
