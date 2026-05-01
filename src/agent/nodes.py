from typing import Literal
from config import DatabaseConfig
from agent.states import AgentState
from agent.db_utils import get_engine, fetch_schema_metadata, metadata_to_ddl
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
    # TODO: Execute generated_sql in db-test container
    
    # Simulate a successful test for now
    test_passed = True 
    
    if test_passed:
        print("Success: SQL is valid.")
        return {"status": "success", "error_log": None}
    else:
        print("Error: SQL execution failed.")
        return {
            "status": "failed", 
            "error_log": "Syntax error at line 1...", 
            "iterations": state["iterations"] + 1
        }

def deploy_node(state: AgentState):
    print("\n[Node: Deployment] Applying changes to Production DB...")
    # TODO: Execute generated_sql in db-prod
    return {"status": "deployed"}

def should_continue(state: AgentState) -> Literal["deploy", "generate", "end"]:
    if state["status"] == "success":
        return "deploy"
    if state["iterations"] < 3:
        return "generate"
    return "end"
