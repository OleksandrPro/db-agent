from typing import Literal
from functools import partial 
from langgraph.graph import StateGraph, START, END
from agent.states import AgentState
from agent.status import NodeStatus, GraphNode
from agent.nodes import (
    introspect_db_node,
    generate_sql_node,
    test_sql_node,
    critic_node,
    deploy_node
)
from agent.llm import get_sql_generation_llm, get_critic_llm
from config import AppSettings
from utils.logging import setup_logger


logger = setup_logger(__name__)

generator_impl = get_sql_generation_llm()
bound_generate_node = partial(generate_sql_node, generator=generator_impl)
critic_impl = get_critic_llm()
bound_critic_node = partial(critic_node, critic=critic_impl)


workflow = StateGraph(AgentState)

workflow.add_node(GraphNode.INTROSPECT, introspect_db_node)
workflow.add_node(GraphNode.GENERATE, bound_generate_node)
workflow.add_node(GraphNode.TEST, test_sql_node)
workflow.add_node(GraphNode.CRITIC, bound_critic_node)
workflow.add_node(GraphNode.DEPLOY, deploy_node)

workflow.add_edge(START, GraphNode.INTROSPECT)
workflow.add_edge(GraphNode.INTROSPECT, GraphNode.GENERATE)
workflow.add_edge(GraphNode.GENERATE, GraphNode.TEST)

def route_after_test(state: AgentState):
    status = state.get("status")
    iterations = state.get("iterations", 0)
    
    if status == NodeStatus.TEST_SUCCESS:
        return GraphNode.CRITIC
        
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
        GraphNode.CRITIC: GraphNode.CRITIC,
        GraphNode.GENERATE: GraphNode.GENERATE,
        END: END
    }
)

def route_after_critic(state: AgentState):
    status = state.get("status")
    iterations = state.get("iterations", 0)
    
    if status == NodeStatus.CRITIC_APPROVED:
        return GraphNode.DEPLOY
        
    if status in (NodeStatus.CRITIC_REJECTED_INTENT, NodeStatus.CRITIC_REJECTED_SAFETY):
        if iterations < AppSettings.MAX_ITERATIONS:
            logger.info(f"Critic rejected. Routing back to generation (Attempt {iterations}/{AppSettings.MAX_ITERATIONS})...")
            return GraphNode.GENERATE
        else:
            logger.error("Max iterations reached after Critic rejection. Stopping.")
            return END
            
    logger.error(f"Critic failed or unknown status: {status}. Stopping.")
    return END

workflow.add_conditional_edges(
    GraphNode.CRITIC,
    route_after_critic,
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
