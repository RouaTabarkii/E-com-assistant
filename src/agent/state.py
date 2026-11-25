<<<<<<< HEAD
from typing import TypedDict

class AgentState(TypedDict, total=False):
    question: str
    route: str                 
    passages: list[dict]      
    answer: str
    citations: list[dict]      
    abstained: bool
=======
"""Shared state that flows through the LangGraph agent."""
from typing import Annotated, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    # Input
    question: str

    # Routing
    route: str                  # "sql" | "docs" | "both" | "out_of_scope"

    # SQL path
    schema_context: str         # output of explain_schema (formatted)
    sql_query: str              # generated SQL
    sql_result: dict            # output of run_sql
    sql_attempts: int           # retry counter (max 3)
    sql_error: str              # last SQL error message if any

    # RAG path
    retrieved_chunks: list[dict]  # output of search_policies

    # Final output
    final_answer: str
    sources_used: list[str]     # "sql" | "docs"

    # Conversation history
    messages: Annotated[list, add_messages]
>>>>>>> 82114d5 (feat(agent): working RAG pipeline with correct embedding model (multilingual-e5-small), Qdrant persistent cache, reorganized nodes)
