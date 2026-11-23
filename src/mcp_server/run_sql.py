import os
import logging
import sqlalchemy
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

load_dotenv()

# --- Logging setup ---
logging.basicConfig(
    filename="logs/sql_queries.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# --- DB Connection (read-only user) ---
DB_URL = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)

# --- Security: forbidden keywords ---
FORBIDDEN = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
    "CREATE", "TRUNCATE", "ATTACH", "PRAGMA",
    "GRANT", "REVOKE", "EXECUTE", "CALL"
}

MAX_ROWS = 100
TIMEOUT_SECONDS = 10


def validate_query(query: str) -> tuple[bool, str]:
    """Check query is safe before execution."""
    q = query.strip().upper()

    # Must start with SELECT or WITH
    if not (q.startswith("SELECT") or q.startswith("WITH")):
        return False, "Only SELECT or WITH queries are allowed."

    # Check for forbidden keywords
    import re
    tokens = set(re.findall(r'\b\w+\b', q))
    found = tokens & FORBIDDEN
    if found:
        return False, f"Forbidden keyword(s) detected: {', '.join(found)}"

    # Reject multiple statements
    if ";" in query.rstrip(";"):
        return False, "Multiple statements are not allowed."

    return True, ""


def run_sql(query: str, limit: int = MAX_ROWS) -> dict:
    """
    Execute a read-only SQL query on the Olist database.

    Args:
        query: SQL SELECT query string
        limit: max rows to return (default 100)

    Returns:
        dict with columns, rows, row_count, duration_ms, or error
    """
    # Validate
    is_valid, error_msg = validate_query(query)
    if not is_valid:
        logger.warning(f"REJECTED | {query} | Reason: {error_msg}")
        return {"error": error_msg}

    # Inject LIMIT if not present
    q = query.strip().rstrip(";")
    if "LIMIT" not in q.upper():
        q = f"{q} LIMIT {limit}"

    # Execute
    try:
        engine = create_engine(
            DB_URL,
            connect_args={"options": "-c statement_timeout=10000"}  # 10s timeout
        )

        start = datetime.now()

        with engine.connect() as conn:
            result = conn.execute(text(q))
            columns = list(result.keys())
            rows = [list(row) for row in result.fetchall()]

        duration_ms = round((datetime.now() - start).total_seconds() * 1000, 2)

        logger.info(f"OK | {duration_ms}ms | {len(rows)} rows | {q}")

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "duration_ms": duration_ms,
            "query_executed": q,
        }

    except sqlalchemy.exc.OperationalError as e:
        logger.error(f"ERROR | {q} | {str(e)}")
        return {"error": f"Database error: {str(e)}"}

    except Exception as e:
        logger.error(f"ERROR | {q} | {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}


if __name__ == "__main__":
    # Quick test
    result = run_sql("SELECT COUNT(*) FROM orders")
    print(result)