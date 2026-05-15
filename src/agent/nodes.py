from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.types import interrupt
from config import settings
from agent.states import AgentState
from agent.status import NodeStatus, ToolOutcome
from agent.orchestrator.protocol import OrchestratorLLM
from agent.classifier.protocol import PromptClassifier
from agent.responses import (
    ClassificationUpdate,
    AgentUpdate,
    ExecuteToolsUpdate,
    HumanReviewUpdate,
    HumanInterruptResponse,
    HumanReviewPayload,
    ToolResult
)
from agent.tools import ToolName
from utils.logging import setup_logger

logger = setup_logger(__name__)

def classify_node(state: AgentState, classifier: PromptClassifier):
    logger.info("Classifying user request...")
    result = classifier.classify(state.user_input)
    
    new_status = NodeStatus.CLASSIFIER_PROCEED if result.status == "proceed" else NodeStatus.CLASSIFIER_OFF_TOPIC
    messages = [HumanMessage(content=state.user_input)] if new_status == NodeStatus.CLASSIFIER_PROCEED else []

    update = ClassificationUpdate(
        status=new_status,
        classification_reasoning=result.reasoning,
        classification_message=result.message,
        messages=messages
    )

    return update.model_dump(exclude_none=True)

def agent_node(state: AgentState, llm: OrchestratorLLM, tools: list):
    logger.info("Agent is thinking...")
    
    system_prompt = """
You are an autonomous Senior DBA Agent. Your goal is to write, test, and validate safe PostgreSQL migrations.

CRITICAL RULE FOR REASONING:
Before you call ANY tool, or before you give a final answer, you MUST write down your thought process. 
Explain WHAT you are doing and WHY. Keep it brief and focused on the next immediate step.
    """
    
    agent_model = llm.bind_tools(tools).with_config({"tags": ["orchestrator"]})
    messages = [SystemMessage(content=system_prompt)] + state.messages
    response = agent_model.invoke(messages)

    update = AgentUpdate(messages=[response])

    return update.model_dump(exclude_none=True)

def execute_tools_node(state: AgentState, tools_map: dict) -> dict:
    logger.info("Executing tools requested by Agent...")
    last_msg = state.messages[-1]
    
    update = ExecuteToolsUpdate(messages=[])
    
    for tool_call in last_msg.tool_calls:
        tool_name_enum = ToolName(tool_call["name"])
        tool_func = tools_map[tool_name_enum]
        
        logger.info(f"-> Running Tool: {tool_name_enum.value}")
        result: ToolResult = tool_func.invoke(tool_call["args"])
        
        update.messages.append(ToolMessage(content=result.llm_message, tool_call_id=tool_call["id"]))
        
        match tool_name_enum:
            case ToolName.GENERATE_SQL:
                if result.outcome == ToolOutcome.SUCCESS:
                    update.generated_sql = result.data
                    update.iterations = state.iterations + 1
                    
            case ToolName.GET_PROD_SCHEMA:
                if result.outcome == ToolOutcome.SUCCESS:
                    update.current_schema = result.data
                    
            case ToolName.GET_SANDBOX_SCHEMA:
                if result.outcome == ToolOutcome.SUCCESS:
                    update.sandbox_schema = result.data
                    
            case ToolName.ASK_CRITIC:
                if result.outcome == ToolOutcome.SUCCESS:
                    update.status = NodeStatus.CRITIC_APPROVED
                    update.migration_summary = result.data
                    
            case ToolName.DEPLOY:
                if result.outcome == ToolOutcome.SUCCESS:
                    update.status = NodeStatus.DEPLOY_SUCCESS
                elif result.outcome == ToolOutcome.DATA_CONFLICT:
                    update.status = NodeStatus.DEPLOY_FAILED_DATA_CONFLICT
                else:
                    update.status = NodeStatus.DEPLOY_FAILED_FATAL

    return update.model_dump(exclude_none=True)

def human_review_node(state: AgentState):
    logger.info("Preparing payload for Human Review...")
    payload = HumanReviewPayload(
        sql=state.generated_sql or "",
        original_schema=state.current_schema or "",
        sandbox_schema=state.sandbox_schema or "",
        migration_summary=state.migration_summary,
        iterations_spent=state.iterations,
        is_stalemate=state.iterations >= settings.max_iterations
    )

    raw_answer = interrupt(payload.model_dump())
    answer = HumanInterruptResponse(**raw_answer)
    
    if answer.action == "approve":
        msg = HumanMessage(content="HUMAN APPROVED. You must now use the execute_production_deployment tool.")
        update = HumanReviewUpdate(
            status=NodeStatus.HUMAN_APPROVED, 
            messages=[msg]
        )
    elif answer.action == "reject":
        feedback_msg = f"HUMAN REVIEW FAILED: {answer.feedback}"
        update = HumanReviewUpdate(
            status=NodeStatus.HUMAN_REJECTED_WITH_FEEDBACK, 
            messages=[HumanMessage(content=feedback_msg)], 
            error_log=feedback_msg, 
            iterations=max(0, state.iterations - 1)
        )
    else:
        update = HumanReviewUpdate(status=NodeStatus.HUMAN_ABORT)

    return update.model_dump(exclude_none=True)