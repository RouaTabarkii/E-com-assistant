"""Tests d'explain_schema sur une base SQLite en mémoire (pas besoin de PostgreSQL)."""
import pytest
from sqlalchemy import create_engine, text

from src.mcp_server.explain_schema import explain_schema, format_schema


@pytest.fixture()
def engine():
    eng = create_engine("sqlite://")
    with eng.begin() as c:
        c.execute(text("CREATE TABLE customers (customer_id TEXT PRIMARY KEY, customer_zip_code_prefix INT)"))
        c.execute(text("CREATE TABLE orders (order_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL, "
                       "order_status TEXT, FOREIGN KEY (customer_id) REFERENCES customers(customer_id))"))
        c.execute(text("CREATE TABLE geolocation (geolocation_zip_code_prefix INT)"))
    return eng


def test_overview_lists_tables_and_relations(engine):
    info = explain_schema(engine=engine)
    assert [t["name"] for t in info["tables"]] == ["customers", "geolocation", "orders"]
    kinds = {(r["from_table"], r["to_table"], r["kind"]) for r in info["relations"]}
    assert ("orders", "customers", "declared") in kinds
    assert ("customers", "geolocation", "logical") in kinds


def test_table_detail(engine):
    info = explain_schema("orders", engine=engine)
    cols = {c["name"]: c for c in info["columns"]}
    assert info["primary_key"] == ["order_id"]
    assert cols["order_id"]["primary_key"] and cols["customer_id"]["foreign_key"]
    assert cols["customer_id"]["nullable"] is False
    assert "delivered" in cols["order_status"]["description"]
    assert info["references"][0]["to_table"] == "customers"


def test_referenced_by(engine):
    info = explain_schema("customers", engine=engine)
    assert any(r["from_table"] == "orders" for r in info["referenced_by"])


def test_case_and_whitespace_insensitive(engine):
    assert explain_schema("  ORDERS ", engine=engine)["table"] == "orders"


@pytest.mark.parametrize("bad", ["nope", "orders; DROP TABLE orders", "pg_catalog.pg_user", "../etc"])
def test_unknown_table_rejected(engine, bad):
    with pytest.raises(ValueError, match="Table inconnue"):
        explain_schema(bad, engine=engine)


@pytest.mark.parametrize("empty", ["", "   ", 42])
def test_invalid_input_rejected(engine, empty):
    with pytest.raises(ValueError):
        explain_schema(empty, engine=engine)


def test_format_schema(engine):
    assert "RELATIONS" in format_schema(explain_schema(engine=engine))
    txt = format_schema(explain_schema("orders", engine=engine))
    assert "PK" in txt and "RÉFÉRENCE" in txt
