from typing import Literal
from functools import partial 
from langgraph.graph import StateGraph, START, END
from agent.states import AgentState
from agent.status import NodeStatus, GraphNode
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

workflow.add_node(GraphNode.INTROSPECT, introspect_db_node)
workflow.add_node(GraphNode.GENERATE, bound_generate_node)
workflow.add_node(GraphNode.TEST, test_sql_node)
workflow.add_node(GraphNode.DEPLOY, deploy_node)

workflow.add_edge(START, GraphNode.INTROSPECT)
workflow.add_edge(GraphNode.INTROSPECT, GraphNode.GENERATE)
workflow.add_edge(GraphNode.GENERATE, GraphNode.TEST)

def route_after_test(state: AgentState):
    status = state.get("status")
    iterations = state.get("iterations", 0)
    
    if status == NodeStatus.TEST_SUCCESS:
        return GraphNode.DEPLOY
        
    if status == NodeStatus.TEST_FAILED_SQL and iterations < AppSettings.MAX_ITERATIONS:
        logger.info(f"Routing back to generation (Attempt {iterations}/{AppSettings.MAX_ITERATIONS})...")
        return GraphNode.GENERATE
        
    if status == NodeStatus.TEST_FAILED_SQL:
        logger.error("Max iterations reached. Stopping.")
        return END
        
    logger.error(f"Fatal error or unknown status: {status}. Stopping.")
    return END

# (Self-Healing Loop)
workflow.add_conditional_edges(
    GraphNode.TEST,
    route_after_test,
    {
        GraphNode.DEPLOY: GraphNode.DEPLOY,
        GraphNode.GENERATE: GraphNode.GENERATE,
        END: END
    }
)

def route_after_deploy(state: AgentState):
    status = state.get("status")
    iterations = state.get("iterations", 0)
    
    if status == NodeStatus.DEPLOY_SUCCESS:
        return END
        
    if status == NodeStatus.DEPLOY_FAILED_DATA_CONFLICT and iterations < AppSettings.MAX_ITERATIONS:
        logger.info(f"Prod data conflict! Routing back to generation (Attempt {iterations}/{AppSettings.MAX_ITERATIONS})...")
        return GraphNode.GENERATE
        
    if status == NodeStatus.DEPLOY_FAILED_DATA_CONFLICT:
        logger.error("Max iterations reached on Prod errors. Stopping.")
        return END
        
    logger.error(f"Fatal deploy error or unknown status: {status}. Stopping.")
    return END

workflow.add_conditional_edges(
    GraphNode.DEPLOY,
    route_after_deploy,
    {
        GraphNode.GENERATE: GraphNode.GENERATE,
        END: END
    }
)

app = workflow.compile()
