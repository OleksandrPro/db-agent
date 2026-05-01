from typing import Literal
from config import DatabaseConfig
from agent.states import AgentState
from utils.db_utils import (
    get_engine,
    fetch_schema_metadata,
    metadata_to_ddl,
    clone_schema,
    apply_sql_query
)
from agent.sql_generation.protocol import SQLGenerator


def introspect_db_node(state: AgentState):
    print("\n[Node: Introspection] Reflecting Production DB schema...")
    
    engine = get_engine(DatabaseConfig.PROD_URL)

    try:
        metadata = fetch_schema_metadata(engine)
        full_schema = metadata_to_ddl(engine, metadata)
        
        print(f"Successfully reflected {len(metadata.tables)} tables.")
        return {"current_schema": full_schema}
            
    except Exception as e:
        print(f"Error during reflection: {e}")
        return {"current_schema": f"Error: {e}", "status": "failed"}
    finally:
        engine.dispose()

def generate_sql_node(state: AgentState, generator: SQLGenerator):
    print(f"\n[Node: Generation] Generating SQL for: {state['user_input']}")

    generated_sql = generator.generate(
        current_schema=state["current_schema"],
        user_input=state["user_input"]
    )
    
    return {"generated_sql": generated_sql}

def test_sql_node(state: AgentState):
    print("\n[Node: Testing] Running SQL in Sandbox...")
    
    prod_engine = get_engine(DatabaseConfig.PROD_URL)
    test_engine = get_engine(DatabaseConfig.TEST_URL)
    
    try:
        clone_schema(prod_engine, test_engine)
        
        generated_sql = state["generated_sql"]
        print(f"Executing: {generated_sql}")
        apply_sql_query(test_engine, generated_sql)
        
        print("Success: SQL is valid and applied to Sandbox.")
        return {"status": "success", "error_log": None}
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error during testing: {error_msg}")
        return {
            "status": "failed", 
            "error_log": error_msg,
            "iterations": state.get("iterations", 0) + 1 
        }
    finally:
        prod_engine.dispose()
        test_engine.dispose()

def deploy_node(state: AgentState):
    print("\n[Node: Deployment] Applying changes to Production DB...")
    
    prod_engine = get_engine(DatabaseConfig.PROD_URL)
    try:
        apply_sql_query(prod_engine, state["generated_sql"])
        print("Success: Changes successfully deployed to Production!")
        return {"status": "deployed"}
    except Exception as e:
        print(f"CRITICAL ERROR during deployment: {e}")
        return {"status": "failed_deploy", "error_log": str(e)}
    finally:
        prod_engine.dispose()

def should_continue(state: AgentState) -> Literal["deploy", "generate", "end"]:
    if state["status"] == "success":
        return "deploy"
    if state["iterations"] < 3:
        return "generate"
    return "end"
