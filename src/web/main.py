from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
import uvicorn

from src.agent.graph import agent

app = FastAPI(title="OlistIQ", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="src/web/static"), name="static")


class HistoryMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class QuestionRequest(BaseModel):
    question: str
    history: list[HistoryMessage] = []


class QuestionResponse(BaseModel):
    question: str
    answer: str
    route: str
    sources_used: list[str]
    sql_query: str | None = None
    sql_columns: list[str] | None = None
    sql_rows: list[list] | None = None
    sql_row_count: int | None = None
    citations: list[dict] | None = None


@app.get("/")
def root():
    return FileResponse("src/web/static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=QuestionResponse)
def ask(request: QuestionRequest):
    # Build LangChain message history
    messages = []
    for msg in request.history:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        else:
            messages.append(AIMessage(content=msg.content))

    result = agent.invoke({
        "question": request.question,
        "messages": messages,
    })

    sql_result = result.get("sql_result", {})

    return QuestionResponse(
        question=request.question,
        answer=result.get("final_answer", ""),
        route=result.get("route", ""),
        sources_used=result.get("sources_used", []),
        sql_query=result.get("sql_query") if "sql" in result.get("sources_used", []) else None,
        sql_columns=sql_result.get("columns") if sql_result else None,
        sql_rows=sql_result.get("rows") if sql_result else None,
        sql_row_count=sql_result.get("row_count") if sql_result else None,
        citations=result.get("retrieved_chunks") if "docs" in result.get("sources_used", []) else None,
    )