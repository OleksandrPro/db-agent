from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class AgentState(TypedDict):
    user_input: str
    agent_response: str

def greeting_node(state: AgentState):
    current_input = state["user_input"]
    response = (
        f"Hello! I am your DB-Agent. You wrote: '{current_input}'. "
        f"I am not connected to the database yet!"
    )
    return {"agent_response": response}

builder = StateGraph(AgentState)
builder.add_node("greeter", greeting_node)

builder.add_edge(START, "greeter")
builder.add_edge("greeter", END)

graph = builder.compile()

if __name__ == "__main__":
    print("=== DB-Agent LangGraph Starter ===")
    user_text = input("Enter a request for the agent: ")
    
    initial_state = {"user_input": user_text, "agent_response": ""}
    result = graph.invoke(initial_state)
    
    print("\n--- Result ---")
    print(result["agent_response"])