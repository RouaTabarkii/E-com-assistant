from langchain_core.messages import HumanMessage
from src.agent.llm import llm
from src.agent.state import AgentState
from src.agent.prompts import ROUTER_PROMPT


def node_route(state: AgentState) -> AgentState:
    """Classify question into sql / docs / both / out_of_scope."""
    prompt = ROUTER_PROMPT.format(question=state["question"])
    response = llm.invoke([HumanMessage(content=prompt)])
    route = response.content.strip().lower()

    if route not in ("sql", "docs", "both", "out_of_scope"):
        route = "out_of_scope"

    print(f"[ROUTE] → {route}")
    return {**state, "route": route, "sql_attempts": 0}