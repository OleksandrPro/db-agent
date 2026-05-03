from typing import Literal
from functools import partial 
from langgraph.graph import StateGraph, START, END
from agent.states import AgentState
from agent.nodes import (
    introspect_db_node,
    generate_sql_node,
    test_sql_node,
    deploy_node
)
from agent.llm import get_sql_generation_llm
from config import AppSettings
from utils.logging import setup_logger


logger = setup_logger(__name__)

generator_impl = get_sql_generation_llm()
bound_generate_node = partial(generate_sql_node, generator=generator_impl)


workflow = StateGraph(AgentState)

workflow.add_node("introspect", introspect_db_node)
workflow.add_node("generate", bound_generate_node)
workflow.add_node("test", test_sql_node)
workflow.add_node("deploy", deploy_node)

workflow.add_edge(START, "introspect")
workflow.add_edge("introspect", "generate")
workflow.add_edge("generate", "test")

def route_after_test(state: AgentState) -> Literal["deploy", "generate", "end"]:
    status = state.get("status")
    iterations = state.get("iterations", 0)
    
    if status == "success":
        return "deploy"
        
    if status == "failed_sql" and iterations < AppSettings.MAX_ITERATIONS:
        logger.info(f"Routing back to generation (Attempt {iterations}/3)...")
        return "generate"
        
    if status == "failed_sql":
        logger.error("Max iterations reached. Stopping.")
        return "end"
        
    logger.error(f"Fatal error or unknown status: {status}. Stopping.")
    return "end"

# (Self-Healing Loop)
workflow.add_conditional_edges(
    "test",
    route_after_test,
    {
        "deploy": "deploy",
        "generate": "generate",
        "end": END
    }
)

workflow.add_edge("deploy", END)

app = workflow.compile()
