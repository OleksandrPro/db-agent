from functools import partial 
from langgraph.graph import StateGraph, START, END
from agent.states import AgentState
from agent.nodes import (
    introspect_db_node,
    generate_sql_node,
    test_sql_node,
    deploy_node,
    should_continue
)
from agent.sql_generation.providers import MockSQLGenerator, GeminiSQLGenerator

generator_impl = MockSQLGenerator()
generator_impl_2 = GeminiSQLGenerator()
bound_generate_node = partial(generate_sql_node, generator=generator_impl)


workflow = StateGraph(AgentState)

workflow.add_node("introspect", introspect_db_node)
workflow.add_node("generate", bound_generate_node)
workflow.add_node("test", test_sql_node)
workflow.add_node("deploy", deploy_node)

workflow.add_edge(START, "introspect")
workflow.add_edge("introspect", "generate")
workflow.add_edge("generate", "test")
workflow.add_conditional_edges(
    "test",
    should_continue,
    {
        "deploy": "deploy",
        "generate": "generate",
        "end": END
    }
)

workflow.add_edge("deploy", END)

app = workflow.compile()
