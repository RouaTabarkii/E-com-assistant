from langchain_core.messages import HumanMessage
from src.agent.llm import llm
from src.agent.state import AgentState
from src.agent.prompts import ROUTER_PROMPT


def node_route(state: AgentState) -> AgentState:
    """Classify question into sql / docs / both / out_of_scope."""
    
    # Build context from history if available
    history_context = ""
    messages = state.get("messages", [])
    if messages:
        history_lines = []
        for msg in messages[-4:]:  # last 2 exchanges
            role = "User" if msg.type == "human" else "Assistant"
            history_lines.append(f"{role}: {msg.content[:200]}")
        history_context = "\n\nConversation history:\n" + "\n".join(history_lines)

    prompt = ROUTER_PROMPT.format(question=state["question"]) + history_context
    response = llm.invoke([HumanMessage(content=prompt)])
    route = response.content.strip().lower()

    if route not in ("sql", "docs", "both", "out_of_scope"):
        route = "out_of_scope"

    print(f"[ROUTE] → {route}")
    return {**state, "route": route, "sql_attempts": 0}