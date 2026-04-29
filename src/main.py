from agent.graph import app


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