import pytest
from src.mcp_server.run_sql import run_sql, validate_query


# --- validate_query tests ---

def test_valid_select():
    is_valid, msg = validate_query("SELECT * FROM orders")
    assert is_valid is True
    assert msg == ""

def test_valid_with():
    is_valid, msg = validate_query("WITH cte AS (SELECT 1) SELECT * FROM cte")
    assert is_valid is True

def test_reject_insert():
    is_valid, msg = validate_query("INSERT INTO orders VALUES (1)")
    assert is_valid is False
    assert "forbidden" in msg.lower() or "allowed" in msg.lower()

def test_reject_drop():
    is_valid, msg = validate_query("DROP TABLE orders")
    assert is_valid is False

def test_reject_delete():
    is_valid, msg = validate_query("DELETE FROM orders")
    assert is_valid is False

def test_reject_update():
    is_valid, msg = validate_query("UPDATE orders SET status='x'")
    assert is_valid is False

def test_reject_multiple_statements():
    is_valid, msg = validate_query("SELECT 1; DROP TABLE orders")
    assert is_valid is False

def test_reject_non_select():
    is_valid, msg = validate_query("PRAGMA table_info(orders)")
    assert is_valid is False


# --- run_sql integration tests ---

def test_run_sql_count():
    result = run_sql("SELECT COUNT(*) FROM orders")
    assert "error" not in result
    assert result["row_count"] == 1
    assert result["rows"][0][0] == 99441

def test_run_sql_limit_injected():
    result = run_sql("SELECT * FROM customers")
    assert "error" not in result
    assert result["row_count"] <= 100
    assert "LIMIT" in result["query_executed"].upper()

def test_run_sql_custom_limit():
    result = run_sql("SELECT * FROM sellers", limit=5)
    assert "error" not in result
    assert result["row_count"] <= 5

def test_run_sql_invalid_query():
    result = run_sql("DROP TABLE orders")
    assert "error" in result

def test_run_sql_bad_table():
    result = run_sql("SELECT * FROM nonexistent_table")
    assert "error" in result

def test_run_sql_returns_columns():
    result = run_sql("SELECT order_id, order_status FROM orders")
    assert "columns" in result
    assert "order_id" in result["columns"]
    assert "order_status" in result["columns"]

def test_run_sql_duration_present():
    result = run_sql("SELECT 1")
    assert "duration_ms" in result
    assert result["duration_ms"] >= 0