from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, START, END

class AgentState(TypedDict):
    user_input: str
    current_schema: Optional[str]
    generated_sql: Optional[str]
    error_log: Optional[str]
    iterations: int
    status: str

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

workflow = StateGraph(AgentState)

workflow.add_node("introspect", introspect_db_node)
workflow.add_node("generate", generate_sql_node)
workflow.add_node("test", test_sql_node)
workflow.add_node("deploy", deploy_node)

workflow.add_edge(START, "introspect")
workflow.add_edge("introspect", "generate")
workflow.add_edge("generate", "test")
workflow.add_conditional_edges(
    "test",
    should_continue,
    {
        "deploy": "deploy",
        "generate": "generate",
        "end": END
    }
)

workflow.add_edge("deploy", END)

app = workflow.compile()


if __name__ == "__main__":
    print("=== DB-Agent MVP (Stub Version) ===")
    user_prompt = input("What DB change do you need? ")
    
    inputs = {
        "user_input": user_prompt,
        "iterations": 0,
        "status": "pending"
    }
    
    for output in app.stream(inputs):
        for key, value in output.items():
            print(f"--- Node '{key}' finished ---")