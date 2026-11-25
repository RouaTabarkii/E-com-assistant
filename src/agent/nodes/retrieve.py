from src.agent.state import AgentState
from src.mcp_server.search_policies import search_policies

TOP_K = 5


def node_retrieve(state: AgentState) -> AgentState:
    """Retrieve relevant policy chunks from Qdrant."""
    try:
        chunks = search_policies(state["question"], k=TOP_K)
    except Exception as e:
        print(f"[RETRIEVE] error: {e}")
        return {**state, "retrieved_chunks": []}
    print(f"[RETRIEVE] {len(chunks)} chunks retrieved")
    return {**state, "retrieved_chunks": chunks}
