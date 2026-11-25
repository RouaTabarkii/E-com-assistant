"""Prompt templates for each node."""

ROUTER_PROMPT = """You are a routing assistant for an e-commerce Q&A system.
Classify the user question into exactly one of these categories:

- sql       : question about data (sales, orders, delivery times, reviews, customers, products)
- docs      : question about company policies (returns, refunds, delivery conditions, warranties, seller rules, reviews moderation, personal data)
- both      : question that needs BOTH data AND policy information
- out_of_scope : question unrelated to e-commerce data or policies

Respond with ONLY one word: sql, docs, both, or out_of_scope.

Question: {question}
"""

SQL_GENERATE_PROMPT = """You are an expert SQL assistant for a PostgreSQL database.
Generate a valid SELECT query to answer the user question.

DATABASE SCHEMA:
{schema}

RULES:
- Only SELECT queries allowed
- Always use lowercase table and column names
- Add a LIMIT clause if the result could be large
- Do not invent column names — use only what is in the schema
- If a previous attempt failed, fix the error described below

{error_context}

Question: {question}

Respond with ONLY the SQL query, no explanation, no markdown.
"""

SYNTHESIZE_PROMPT = """You are a helpful e-commerce assistant. 
Compose a clear, accurate answer to the user question using the provided sources.

RULES:
- Only use information from the provided sources
- If SQL results are provided, reference exact numbers
- If policy chunks are provided, cite them as [Document Title, Section X]
- Clearly separate what comes from data vs what comes from policies
- If a source is missing, say so — never invent information
- Answer in the same language as the question

Question: {question}

{sql_section}

{docs_section}

Answer:
"""