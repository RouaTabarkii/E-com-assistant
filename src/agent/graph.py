from langgraph.graph import StateGraph, END
from src.agent.state import AgentState
from src.agent.nodes import (
    node_route,
    node_schema,
    node_sql_generate,
    node_sql_execute,
    node_retrieve,
    node_synthesize,
    node_guardrails,
)
from src.agent.nodes.sql_execute import MAX_SQL_ATTEMPTS


def should_retry_sql(state: AgentState) -> str:
    if state.get("sql_error") and state.get("sql_attempts", 0) < MAX_SQL_ATTEMPTS:
        return "retry"
    return "done"


def route_question(state: AgentState) -> str:
    return state["route"]


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("route",        node_route)
    graph.add_node("guardrails",   node_guardrails)
    graph.add_node("schema",       node_schema)
    graph.add_node("sql_generate", node_sql_generate)
    graph.add_node("sql_execute",  node_sql_execute)
    graph.add_node("retrieve",     node_retrieve)
    graph.add_node("synthesize",   node_synthesize)

    graph.set_entry_point("route")

    graph.add_conditional_edges(
        "route",
        route_question,
        {
            "sql":          "schema",
            "docs":         "retrieve",
            "both":         "schema",
            "out_of_scope": "guardrails",
        }
    )

    graph.add_edge("schema",       "sql_generate")
    graph.add_edge("sql_generate", "sql_execute")
    graph.add_conditional_edges(
        "sql_execute",
        should_retry_sql,
        {
            "retry": "sql_generate",
            "done":  "synthesize",
        }
    )

    graph.add_edge("retrieve",   "synthesize")
    graph.add_edge("synthesize", END)
    graph.add_edge("guardrails", END)

    return graph.compile()


agent = build_graph()


if __name__ == "__main__":
    result = agent.invoke({
        "question": "Quel est le délai de rétractation pour un produit acheté ?",
        "messages": [],
    })
    print("\n=== FINAL ANSWER ===")
    print(result["final_answer"])
    print("\nSources used:", result["sources_used"])
