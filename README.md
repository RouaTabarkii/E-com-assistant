# E-commerce Assistant

An intelligent conversational assistant designed to answer natural language questions about e-commerce business data and company policies.

The system combines **Text-to-SQL**, **Retrieval-Augmented Generation (RAG)**, and **AI Agent orchestration** to provide accurate, verifiable, and context-aware answers using the Olist Brazilian E-Commerce dataset and company policy documents.

## Project Overview

E-commerce teams frequently need to answer two types of questions:

- **Data-related questions:** Sales, orders, delivery times, customer reviews, and other business metrics stored in relational databases.
- **Policy-related questions:** Returns, refunds, warranties, delivery conditions, and other internal procedures described in company documents.

This project aims to unify these information sources through a conversational AI assistant capable of automatically identifying the type of question and selecting the appropriate tools.

## Key Features

- **Intelligent Query Routing:** Automatically classifies questions into data-related, policy-related, hybrid, or out-of-scope categories.
- **Text-to-SQL:** Converts natural language questions into SQL queries and executes them against the Olist database in read-only mode.
- **Retrieval-Augmented Generation (RAG):** Retrieves relevant information from company policy documents and generates grounded answers with precise citations.
- **Hybrid Question Answering:** Combines database queries and document retrieval to answer questions requiring both sources.
- **AI Agent Orchestration:** Uses LangGraph to manage workflows, routing, tool calls, and response generation.
- **MCP Integration:** Exposes reusable tools through the Model Context Protocol (MCP).
- **Web Interface:** Provides a conversational interface with SQL queries, database results, and document citations.
- **Benchmarking & Evaluation:** Measures retrieval quality, SQL execution accuracy, routing performance, and answer faithfulness.

## Data Sources

### 1. Olist Brazilian E-Commerce Dataset

The project uses the public Brazilian E-Commerce dataset by Olist, which contains information about:

- Customers and sellers
- Orders and order items
- Payments
- Customer reviews
- Products and categories
- Geolocation data

The CSV files are loaded into a relational database (SQLite or PostgreSQL) to support natural language querying.

### 2. Company Policy Documents

A collection of policy documents in PDF, Markdown, or DOCX format, covering topics such as:

- Return and withdrawal policies
- Refund procedures
- Delivery conditions and delays
- Product warranties and after-sales service
- Marketplace seller policies
- Customer review moderation
- Personal data protection

These documents are processed and indexed in a vector database to support semantic retrieval.

## Technical Architecture

The system is organized into four main layers:

1. **Web Interface:** Handles user questions and displays answers, SQL queries, results, and document citations.
2. **AI Agent (LangGraph):** Classifies questions, orchestrates workflows, invokes tools, and synthesizes final responses.
3. **MCP Server:** Exposes database and document retrieval capabilities through reusable tools.
4. **Storage Layer:** Contains the relational Olist database and the vector database used for policy documents.

## Technology Stack

| Component | Technologies |
|---|---|
| Programming Language | Python 3.11+ |
| LLM Orchestration | LangChain, LangGraph |
| Tool Integration | Model Context Protocol (MCP) |
| Database | SQLite / PostgreSQL |
| Vector Database | Chroma / FAISS / pgvector |
| Embeddings | Multilingual E5 / BGE-M3 |
| Interface | Streamlit / Gradio |
| Evaluation | Ragas, Pytest, Custom Python Scripts |
| Deployment | Docker, Docker Compose |

*The final technology choices may be adjusted during implementation.*

## MCP Tools

The MCP server will expose three main tools:

| Tool | Description |
|---|---|
| `run_sql` | Executes validated, read-only SQL queries against the Olist database. |
| `search_policies` | Retrieves relevant passages from company policy documents. |
| `explain_schema` | Provides information about database tables, columns, and relationships. |

## Project Structure

```text
ecom-assistant/
│
├── data/
│   ├── olist/
│   ├── policies/
│   └── eval/
│
├── src/
│   ├── ingestion/
│   ├── mcp_server/
│   ├── agent/
│   ├── web/
│   └── evaluation/
│
├── tests/
├── docs/
│
├── docker-compose.yml
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

## Evaluation

The assistant will be evaluated using an annotated benchmark containing at least 50 questions:

- 20 data-related questions.
- 20 policy-related questions.
- 10 hybrid or out-of-scope questions.

Evaluation metrics include:

- Routing Accuracy
- SQL Execution Accuracy
- Valid SQL Query Rate
- Recall@K and Precision@K
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain (nDCG)
- Answer Faithfulness
- Answer Relevance
- Citation Accuracy
- Correct Abstention Rate
- Response Latency and Cost

## Security and Reliability

The system follows several security and reliability principles:

- Read-only database access.
- SQL query validation and execution limits.
- Protection against SQL injection.
- Protection against prompt injection in retrieved documents.
- API keys stored in environment variables.
- Source-grounded answers with verifiable citations.
- Explicit handling of errors and missing information.

## Team

| Member |
|---|
| Ayett MANSOURI |
| Mohamed Haroun MEZNED |
| Roua Tabarki |

## Project Status

**Status:** In Development

This project is being developed as part of an academic engineering project.
