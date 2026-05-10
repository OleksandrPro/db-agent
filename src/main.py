import uuid
import asyncio
from langgraph.types import Command
from agent.graph import app
from agent.responses import HumanInterruptResponse, HumanReviewPayload
from agent.status import GraphNode
from utils.logging import setup_logger
from utils.events import AgentEventWriter, LoggerEventWriter

logger = setup_logger(__name__)

async def process_graph_events(graph_app, inputs, config, writer: AgentEventWriter):
    async for event in graph_app.astream_events(inputs, config=config, version="v2"):
        kind = event["event"]
        
        if kind == "on_chat_model_end":
            ai_message = event["data"]["output"]
            if hasattr(ai_message, "content") and ai_message.content:
                thought = ai_message.content.strip()
                if thought:
                    writer.on_thought(thought)
                    
        elif kind == "on_tool_start":
            tool_name = event["name"]
            writer.on_tool_start(tool_name)

async def main():
    logger.info("=== DB-Agent MVP 4.0 (Autonomous Agent Workflow) ===")
    user_prompt = input("What DB change do you need? ")
    
    logger.info(f"User prompt: {user_prompt}")

    inputs = {
        "user_input": user_prompt
    }
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    logger_writer = LoggerEventWriter(logger=logger)
    
    logger.info("Starting graph execution...")

    await process_graph_events(app, inputs, config, writer=logger_writer)
    
    snapshot = app.get_state(config)
    
    while snapshot.next:
        if GraphNode.HUMAN_REVIEW in snapshot.next:
            tasks = snapshot.tasks
            if not tasks or not tasks[0].interrupts:
                break
                
            interrupt_data = tasks[0].interrupts[0].value
            payload = HumanReviewPayload(**interrupt_data)
            
            logger.warning("=" * 50)
            logger.warning("ATTENTION: HUMAN REVIEW REQUIRED")
            logger.warning("=" * 50)

            print(f"\n[Changes summary]:\n{payload.migration_summary}\n")
            print(f"[SQL for deployment]:\n{payload.sql}\n")
            
            if payload.is_stalemate:
                logger.warning("AGENT STALEMATE: Max iterations reached. Agent is stuck.")
            logger.warning("=" * 50)
            
            choice = input("\nApprove deployment? (y - approve, n - revise, q - abort): ").strip().lower()
            
            if choice == 'y':
                action = "approve"
                feedback = None
                logger.info("Deployment approved. Giving agent the green light...")
            elif choice == 'q':
                action = "abort"
                feedback = None
                logger.info("Aborting deployment...")
            else:
                action = "reject"
                feedback = input("What should the agent fix? ")
                logger.info("Returning to the agent for revision...")

            user_decision = HumanInterruptResponse(action=action, feedback=feedback)
            
            resume_command = Command(resume=user_decision.model_dump())
            await process_graph_events(app, resume_command, config, writer=logger_writer)
        else:
            break
            
    final_state = app.get_state(config).values
    logger.info(f"Graph execution finished. Final status: {final_state.get('status')}")

if __name__ == "__main__":
    asyncio.run(main())