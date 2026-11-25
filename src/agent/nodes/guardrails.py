from src.agent.state import AgentState

MAX_SQL_ATTEMPTS = 3


def node_guardrails(state: AgentState) -> AgentState:
    """Handle out_of_scope and max retries exceeded."""
    if state["route"] == "out_of_scope":
        return {
            **state,
            "final_answer": (
                "Cette question est hors de mon périmètre. "
                "Je peux uniquement répondre à des questions sur les données "
                "Olist ou les politiques de l'entreprise."
            ),
            "sources_used": [],
        }

    if state.get("sql_attempts", 0) >= MAX_SQL_ATTEMPTS and state.get("sql_error"):
        return {
            **state,
            "final_answer": (
                f"Impossible de générer une requête SQL valide après "
                f"{MAX_SQL_ATTEMPTS} tentatives. "
                f"Dernière erreur : {state['sql_error']}"
            ),
            "sources_used": [],
        }

    return state