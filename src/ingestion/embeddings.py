"""Calcul des embeddings (BAAI/bge-m3 par défaut, multilingual-e5 en option).

Ce module est partagé par l'indexation (index_policies.py) et par la recherche
(outil MCP `search_policies`) : documents et requêtes DOIVENT être encodés avec
le même modèle et les mêmes conventions, sinon la similarité n'a aucun sens.

Usage côté recherche :
    from ingestion.embeddings import load_model, embed_queries
    model = load_model("BAAI/bge-m3")
    vec = embed_queries(model, ["Quel est le délai de rétractation ?"])[0]
"""
from __future__ import annotations

from dataclasses import dataclass

DEFAULT_MODEL = "BAAI/bge-m3"

# Conventions propres à chaque famille de modèles.
#  - bge-m3 : aucun préfixe requis, 1024 dimensions, contexte jusqu'à 8192 tokens.
#  - e5     : préfixes "passage: " / "query: " OBLIGATOIRES (sinon qualité dégradée).
@dataclass(frozen=True)
class ModelSpec:
    doc_prefix: str = ""
    query_prefix: str = ""
    max_seq_length: int = 512  # nos chunks font < 300 tokens ; évite de réserver 8192


def spec_for(model_name: str) -> ModelSpec:
    name = model_name.lower()
    if "e5" in name:
        return ModelSpec(doc_prefix="passage: ", query_prefix="query: ")
    return ModelSpec()  # bge-m3 et autres


def load_model(model_name: str = DEFAULT_MODEL, device: str | None = None):
    """Charge le modèle (téléchargement au premier appel, ~2 Go pour bge-m3)."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name, device=device)
    model.max_seq_length = spec_for(model_name).max_seq_length
    model._embedding_model_name = model_name  # mémorisé pour choisir les préfixes
    return model


def build_embedding_text(chunk: dict) -> str:
    """Texte réellement encodé pour un chunk.

    On préfixe le titre du document et de la section : « Délai » seul ne dit pas de quelle
    politique on parle. Le payload stocké garde, lui, le texte original (pour les citations).
    """
    meta = chunk.get("metadata", {})
    header = " — ".join(p for p in (meta.get("title"), meta.get("section_title")) if p)
    return f"{header}\n{chunk['text']}" if header else chunk["text"]


def embed_documents(model, texts: list[str], batch_size: int = 32, show_progress: bool = True):
    prefix = spec_for(getattr(model, "_embedding_model_name", DEFAULT_MODEL)).doc_prefix
    return model.encode(
        [prefix + t for t in texts],
        batch_size=batch_size,
        show_progress_bar=show_progress,
        normalize_embeddings=True,  # cosinus == produit scalaire
    )


def embed_queries(model, queries: list[str], batch_size: int = 32):
    prefix = spec_for(getattr(model, "_embedding_model_name", DEFAULT_MODEL)).query_prefix
    return model.encode(
        [prefix + q for q in queries],
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
