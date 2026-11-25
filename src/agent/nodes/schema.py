from src.agent.state import AgentState
from src.mcp_server.explain_schema import explain_schema, format_schema


def node_schema(state: AgentState) -> AgentState:
    """Fetch and format the DB schema to give context to SQL generation."""
    schema_info = explain_schema()
    schema_text = format_schema(schema_info)
    print(f"[SCHEMA] fetched ({len(schema_text)} chars)")
    return {**state, "schema_context": schema_text}