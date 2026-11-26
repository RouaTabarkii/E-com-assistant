from src.agent.state import AgentState
from src.mcp_server.explain_schema import explain_schema, format_schema


IMPORTANT_TABLES = ["orders", "order_items", "order_payments", "order_reviews", "products", "customers", "sellers"]


def node_schema(state: AgentState) -> AgentState:
    """Fetch full schema overview + detailed columns for key tables."""
    
    # Overview
    schema_info = explain_schema()
    overview = format_schema(schema_info)
    
    # Detailed columns for important tables
    details = []
    for table in IMPORTANT_TABLES:
        try:
            detail = explain_schema(table=table)
            details.append(format_schema(detail))
        except Exception:
            pass
    
    schema_text = overview + "\n\n" + "\n\n".join(details)
    print(f"[SCHEMA] fetched ({len(schema_text)} chars)")
    return {**state, "schema_context": schema_text}