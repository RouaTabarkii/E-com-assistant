"""Tests unitaires de search_policies — Qdrant et le modèle sont mockés."""
import sys
import numpy as np
import pytest
from unittest.mock import MagicMock, patch


# ------------------------------------------------------------------ #
# Fake objects                                                         #
# ------------------------------------------------------------------ #
def make_fake_model():
    fake_model = MagicMock()
    fake_model._embedding_model_name = "BAAI/bge-m3"
    fake_model.encode.return_value = np.ones((1, 4), dtype="float32")
    return fake_model


def make_fake_point():
    fake_point = MagicMock()
    fake_point.score = 0.92
    fake_point.payload = {
        "chunk_id": 0,
        "doc_id": "POL-RET-001",
        "title": "Politique de retour",
        "doc_type": "retour",
        "version": "1.0",
        "section": "1. Délai de rétractation",
        "clauses": None,
        "citation": "[Politique de retour, section 1, p.1]",
        "text": "Le client dispose de 14 jours pour se rétracter.",
    }
    return fake_point


def make_fake_client(points=None):
    fake_response = MagicMock()
    fake_response.points = points if points is not None else [make_fake_point()]
    fake_client = MagicMock()
    fake_client.query_points.return_value = fake_response
    return fake_client


# ------------------------------------------------------------------ #
# Patch BEFORE any import of search_policies                          #
# ------------------------------------------------------------------ #
fake_model = make_fake_model()
fake_client = make_fake_client()

# Remove cached module if already imported
sys.modules.pop("src.mcp_server.search_policies", None)

with patch("src.ingestion.embeddings.load_model", return_value=fake_model), \
     patch("qdrant_client.QdrantClient", return_value=fake_client):
    import src.mcp_server.search_policies as sp
    # Inject mocks directly into module namespace
    sp.client = fake_client
    sp.model = fake_model


# ------------------------------------------------------------------ #
# Tests de validation des entrées                                      #
# ------------------------------------------------------------------ #
def test_empty_question_raises():
    with pytest.raises(ValueError, match="vide"):
        sp.search_policies("   ")

def test_blank_question_raises():
    with pytest.raises(ValueError):
        sp.search_policies("")

def test_k_zero_raises():
    with pytest.raises(ValueError):
        sp.search_policies("question valide", k=0)

def test_k_too_large_raises():
    with pytest.raises(ValueError):
        sp.search_policies("question valide", k=11)

def test_k_negative_raises():
    with pytest.raises(ValueError):
        sp.search_policies("question valide", k=-1)


# ------------------------------------------------------------------ #
# Tests de structure de la réponse                                     #
# ------------------------------------------------------------------ #
def test_returns_list():
    result = sp.search_policies("Quel est le délai de rétractation ?")
    assert isinstance(result, list)

def test_result_has_required_keys():
    result = sp.search_policies("délai de retour")
    assert len(result) > 0
    keys = {"chunk_id", "score", "doc_id", "title", "doc_type",
            "version", "section", "clauses", "citation", "text"}
    assert keys == set(result[0].keys())

def test_score_is_rounded():
    result = sp.search_policies("retour produit")
    assert result[0]["score"] == round(result[0]["score"], 4)

def test_correct_doc_id_returned():
    result = sp.search_policies("rétractation")
    assert result[0]["doc_id"] == "POL-RET-001"


# ------------------------------------------------------------------ #
# Tests des filtres metadata                                           #
# ------------------------------------------------------------------ #
def test_filter_doc_type_passed_to_qdrant():
    sp.search_policies("retour", doc_type="retour")
    call_kwargs = fake_client.query_points.call_args.kwargs
    f = call_kwargs["query_filter"]
    assert f is not None
    assert any(c.key == "doc_type" for c in f.must)

def test_filter_doc_id_passed_to_qdrant():
    sp.search_policies("retour", doc_id="POL-RET-001")
    call_kwargs = fake_client.query_points.call_args.kwargs
    f = call_kwargs["query_filter"]
    assert any(c.key == "doc_id" for c in f.must)

def test_filter_version_passed_to_qdrant():
    sp.search_policies("retour", version="1.0")
    call_kwargs = fake_client.query_points.call_args.kwargs
    f = call_kwargs["query_filter"]
    assert any(c.key == "version" for c in f.must)

def test_no_filter_when_no_params():
    sp.search_policies("retour")
    call_kwargs = fake_client.query_points.call_args.kwargs
    assert call_kwargs["query_filter"] is None

def test_k_passed_to_qdrant():
    sp.search_policies("retour", k=5)
    call_kwargs = fake_client.query_points.call_args.kwargs
    assert call_kwargs["limit"] == 5

def test_empty_results_returns_empty_list():
    sp.client = make_fake_client(points=[])
    result = sp.search_policies("question sans résultat")
    assert result == []
    sp.client = fake_client  # restore