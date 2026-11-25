from src.agent.state import AgentState
from src.mcp_server.run_sql import run_sql

MAX_SQL_ATTEMPTS = 3


def node_sql_execute(state: AgentState) -> AgentState:
    """Execute the generated SQL query, track errors for retry loop."""
    result = run_sql(state["sql_query"])
    attempts = state.get("sql_attempts", 0) + 1

    if "error" in result:
        print(f"[SQL_EXECUTE] error: {result['error']}")
        return {
            **state,
            "sql_result": {},
            "sql_error": result["error"],
            "sql_attempts": attempts,
        }

    print(f"[SQL_EXECUTE] ok — {result['row_count']} rows in {result['duration_ms']}ms")
    return {
        **state,
        "sql_result": result,
        "sql_error": "",
        "sql_attempts": attempts,
    }