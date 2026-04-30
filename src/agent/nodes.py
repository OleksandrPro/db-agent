from typing import Literal
from sqlalchemy import create_engine, MetaData
from sqlalchemy.schema import CreateTable
from config import DatabaseConfig
from agent.states import AgentState


def introspect_db_node(state: AgentState):
    print("\n[Node: Introspection] Reflecting Production DB schema...")
    
    engine = create_engine(DatabaseConfig.PROD_URL)
    
    try:
        with engine.connect() as connection:
            metadata = MetaData()
            metadata.reflect(bind=engine)
            
            ddl_statements = []
            
            for table_name in metadata.tables:
                table_obj = metadata.tables[table_name]
                
                ddl = str(CreateTable(table_obj).compile(engine))
                ddl_statements.append(ddl.strip() + ";")
            
            full_schema = "\n\n".join(ddl_statements)
            
            if not ddl_statements:
                full_schema = "Database is empty."
                
            print(f"Successfully reflected {len(ddl_statements)} tables.")
            return {"current_schema": full_schema}
            
    except Exception as e:
        print(f"Error during reflection: {e}")
        return {"current_schema": f"Error: {e}", "status": "failed"}
    finally:
        engine.dispose()

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
