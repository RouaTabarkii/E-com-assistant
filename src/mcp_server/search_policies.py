from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from src.ingestion.embeddings import embed_queries, load_model

client = QdrantClient(url="http://localhost:6333")
model = load_model()

COLLECTION = "policies"
MAX_K = 10


def build_filter(doc_type=None, doc_id=None, version=None):
    """Construit le filtre Qdrant à partir des paramètres non vides."""
    conditions = []
    if doc_type is not None:
        conditions.append(FieldCondition(key="doc_type", match=MatchValue(value=doc_type)))
    if doc_id is not None:
        conditions.append(FieldCondition(key="doc_id", match=MatchValue(value=doc_id)))
    if version is not None:
        conditions.append(FieldCondition(key="version", match=MatchValue(value=str(version))))
    return Filter(must=conditions) if conditions else None


def search_policies(question, k=3, doc_type=None, doc_id=None, version=None):
    """Renvoie une liste de dictionnaires : les k chunks les plus proches."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("La question ne peut pas être vide.")
    if not isinstance(k, int) or not 1 <= k <= MAX_K:
        raise ValueError(f"k doit être un entier entre 1 et {MAX_K}.")

    vector = embed_queries(model, [question.strip()])[0].tolist()
    response = client.query_points(
        collection_name=COLLECTION,
        query=vector,
        query_filter=build_filter(doc_type, doc_id, version),
        limit=k,
        with_payload=True,
    )

    results = []
    for p in response.points:
        pl = p.payload
        results.append({
            "chunk_id": pl.get("chunk_id"),
            "score": round(p.score, 4),
            "doc_id": pl.get("doc_id"),
            "title": pl.get("title"),
            "doc_type": pl.get("doc_type"),
            "version": pl.get("version"),
            "section": pl.get("section"),
            "clauses": pl.get("clauses"),
            "citation": pl.get("citation"),
            "text": pl.get("text"),
        })
    return results  

def show(results):
    if not results:
        print("   (aucun résultat)")
    for r in results:
        print(f"{r['score']:.3f} | {r['chunk_id']} | {r['citation']}")
        print("   ", (r["text"] or "")[:100])


if __name__ == "__main__":
    q = "Quel est le délai de rétractation ?"

    show(search_policies(q))
    show(search_policies(q, doc_type="remboursement"))
    show(search_policies(q, doc_id="POL-RET-001"))
    show(search_policies(q, doc_type="xyz"))
    show(search_policies(q, doc_type="retour", version="2.0"))
    try:
        search_policies("   ")
    except ValueError as e:
        print("   Erreur attendue :", e)