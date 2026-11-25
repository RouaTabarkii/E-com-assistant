from langchain_core.messages import HumanMessage
from src.agent.llm import llm
from src.agent.state import AgentState
from src.agent.prompts import SQL_GENERATE_PROMPT


def node_sql_generate(state: AgentState) -> AgentState:
    """Generate a SQL query from the question and schema."""
    error_context = ""
    if state.get("sql_error"):
        error_context = (
            f"PREVIOUS ERROR (attempt {state['sql_attempts']}):\n"
            f"{state['sql_error']}\nPlease fix the query."
        )

    prompt = SQL_GENERATE_PROMPT.format(
        schema=state["schema_context"],
        question=state["question"],
        error_context=error_context,
    )

    response = llm.invoke([HumanMessage(content=prompt)])

    sql_query = response.content.strip()
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

    if sql_query.lower().startswith("elect "):
        sql_query = "S" + sql_query

    print(f"[SQL_GENERATE] attempt {state['sql_attempts'] + 1}: {sql_query[:80]}...")
    return {**state, "sql_query": sql_query}