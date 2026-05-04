from agent.graph import app
from utils.logging import setup_logger


logger = setup_logger(__name__)

if __name__ == "__main__":
    logger.info("=== DB-Agent MVP (Agent Workflow) ===")
    user_prompt = input("What DB change do you need? ")
    
    inputs = {
        "user_input": user_prompt,
        "iterations": 0,
        "status": "pending"
    }
    
    for output in app.stream(inputs):
        for key, value in output.items():
            logger.info(f"--- Node '{key}' finished ---")