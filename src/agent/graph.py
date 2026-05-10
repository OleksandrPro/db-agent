from functools import partial 
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from agent.states import AgentState
from agent.status import NodeStatus, GraphNode
from agent.nodes import (
    classify_node,
    agent_node,
    execute_tools_node,
    human_review_node,
)
from agent.llm import (
    get_classifier_llm, 
    get_agent_llm, 
    get_sql_generation_llm, 
    get_critic_llm
)
from agent.tools import (
    ToolName,
    get_database_schema,
    make_sql_generation_tool,
    test_sql_in_sandbox,
    make_critic_tool,
    execute_production_deployment
)
from config import settings
from utils.logging import setup_logger

logger = setup_logger(__name__)

classifier_impl = get_classifier_llm()
orchestrator_impl = get_agent_llm()
generator_impl = get_sql_generation_llm()
critic_impl = get_critic_llm()

generate_sql_tool = make_sql_generation_tool(generator_impl)
critic_tool = make_critic_tool(critic_impl)

tools_list = [
    get_database_schema, 
    generate_sql_tool, 
    test_sql_in_sandbox, 
    critic_tool, 
    execute_production_deployment
]

tools_map = {
    ToolName.GET_SCHEMA: get_database_schema,
    ToolName.GENERATE_SQL: generate_sql_tool,
    ToolName.TEST_SQL: test_sql_in_sandbox,
    ToolName.ASK_CRITIC: critic_tool,
    ToolName.DEPLOY: execute_production_deployment
}

bound_classify_node = partial(classify_node, classifier=classifier_impl)
bound_agent_node = partial(agent_node, llm=orchestrator_impl, tools=tools_list)
bound_execute_tools_node = partial(execute_tools_node, tools_map=tools_map)

workflow = StateGraph(AgentState)

workflow.add_node(GraphNode.CLASSIFY, bound_classify_node)
workflow.add_node(GraphNode.AGENT, bound_agent_node)
workflow.add_node(GraphNode.TOOLS, bound_execute_tools_node)
workflow.add_node(GraphNode.HUMAN_REVIEW, human_review_node)

workflow.add_edge(START, GraphNode.CLASSIFY)

def route_after_classification(state: AgentState):
    return GraphNode.AGENT if state.status == NodeStatus.CLASSIFIER_PROCEED else END

workflow.add_conditional_edges(
    GraphNode.CLASSIFY,
    route_after_classification,
    {
        GraphNode.AGENT: GraphNode.AGENT,
        END: END
    }
)

def route_after_agent(state: AgentState):
    last_message = state.messages[-1]
    
    if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
        return GraphNode.TOOLS
    
    if state.status in [NodeStatus.DEPLOY_SUCCESS, NodeStatus.DEPLOY_FAILED_FATAL]:
        return END
        
    if state.status == NodeStatus.CRITIC_APPROVED:
        return GraphNode.HUMAN_REVIEW
        
    if state.iterations >= settings.max_iterations:
        logger.warning("Max iterations reached. Forcing Human Review.")
        return GraphNode.HUMAN_REVIEW

    logger.info("Agent stopped autonomously without reaching a designated goal.")
    return END

workflow.add_conditional_edges(
    GraphNode.AGENT,
    route_after_agent, {
        GraphNode.TOOLS: GraphNode.TOOLS,
        GraphNode.HUMAN_REVIEW: GraphNode.HUMAN_REVIEW,
        GraphNode.AGENT: GraphNode.AGENT,
        END: END
    }
)

workflow.add_edge(GraphNode.TOOLS, GraphNode.AGENT)

def route_after_human(state: AgentState):
    if state.status in [NodeStatus.HUMAN_APPROVED, NodeStatus.HUMAN_REJECTED_WITH_FEEDBACK]:
        return GraphNode.AGENT
    return END

workflow.add_conditional_edges(
    GraphNode.HUMAN_REVIEW,
    route_after_human, {
        GraphNode.AGENT: GraphNode.AGENT,
        END: END
    }
)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)