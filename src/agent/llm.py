import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model=os.getenv("LLM_MODEL", "openai/gpt-oss-120b"),
    temperature=0,
)