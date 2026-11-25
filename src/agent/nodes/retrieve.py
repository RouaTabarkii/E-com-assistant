from src.mcp_server.search_policies import search_policies 

TOP_K = 5

def retrieve(state: dict) -> dict:
    """Nœud retrieve : appelle l'outil search_policies."""
    try:
        passages = search_policies(state["question"], k=TOP_K)
    except Exception as e:          
        return {"passages": [], "error": str(e)}
    return {"passages": passages}