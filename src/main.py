import uuid
from langgraph.types import Command
from agent.graph import app
from utils.logging import setup_logger


logger = setup_logger(__name__)

if __name__ == "__main__":
    logger.info("=== DB-Agent MVP (Console HITL Workflow) ===")
    user_prompt = input("What DB change do you need? ")
    
    logger.info(f"User prompt: {user_prompt}")

    inputs = {
        "user_input": user_prompt,
        "iterations": 0,
        "status": "pending"
    }
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    logger.info("Starting graph execution...")
    result = app.invoke(inputs, config=config)
    
    while "__interrupt__" in result:
        interrupt_payload = result["__interrupt__"][0].value
        
        logger.warning("=" * 50)
        logger.warning("ATTENTION: HUMAN REVIEW REQUIRED")
        logger.warning("=" * 50)
        logger.info(f"Changes summary:\n{interrupt_payload.get('migration_summary')}\n")
        logger.info(f"SQL for deployment:\n{interrupt_payload.get('sql')}\n")
        logger.info(f"Critic Feedback: {interrupt_payload.get('critic_logs')}")
        
        if interrupt_payload.get('is_stalemate'):
            logger.warning("Agent has reached a stalemate (max iterations reached).")
        logger.warning("=" * 50)
        
        choice = input("\nApprove deployment? (y - yes, n - revise, q - abort): ").strip().lower()
        
        choice = choice.lower()

        if choice == 'y':
            user_decision = {"action": "approve"}
            logger.info("Deployment approved. Proceeding...")
        elif choice == 'q':
            user_decision = {"action": "abort"}
            logger.info("Aborting deployment...")
        else:
            feedback = input("What should the agent fix? ")
            user_decision = {"action": "reject", "feedback": feedback}
            logger.info("Returning to the agent for revision...")

        result = app.invoke(Command(resume=user_decision), config=config)
        
    logger.info(f"Graph execution finished. Final status: {result.get('status')}")