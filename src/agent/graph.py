from langgraph.graph import StateGraph, START, END
from src.agent.state import AgentState
from src.agent.nodes.retrieve import retrieve
from src.agent.nodes.synthesize import synthesize

def build_graph():
    g = StateGraph(AgentState)
    g.add_node("retrieve", retrieve)
    g.add_node("synthesize", synthesize)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "synthesize")
    g.add_edge("synthesize", END)
    return g.compile()

if __name__ == "__main__":
    out = build_graph().invoke({"question": "Combien de jours pour me rétracter ?"})
    print(out["answer"]); print(out["citations"])