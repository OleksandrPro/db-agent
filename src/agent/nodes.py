from typing import Literal
from .states import AgentState


def introspect_db_node(state: AgentState):
    print("\n[Node: Introspection] Reading database schema...")
    # TODO: Connect to DB and fetch tables/columns
    return {"current_schema": "table_users(id, name, email)", "iterations": 0}

def generate_sql_node(state: AgentState):
    print(f"\n[Node: Generation] Generating SQL for: {state['user_input']}")
    # TODO: Pass schema + input to Gemini
    # Placeholder SQL
    return {"generated_sql": "ALTER TABLE table_users ADD COLUMN age INTEGER;"}

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
