"""Indexation des politiques dans Qdrant : embeddings (bge-m3 par défaut) + métadonnées.

    python src/ingestion/index_policies.py                       # bge-m3, Qdrant sur localhost:6333
    python src/ingestion/index_policies.py --model intfloat/multilingual-e5-base --collection policies_e5
    python src/ingestion/index_policies.py --qdrant-path data/qdrant   # sans serveur (fichiers locaux)

Une collection par modèle (ex. `policies` pour bge-m3, `policies_e5`) permet de comparer
les modèles lors de l'évaluation de la récupération sans réindexer à chaque fois.
"""
import argparse
import json
import sys
import uuid
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embeddings import DEFAULT_MODEL, build_embedding_text, embed_documents, load_model  # noqa: E402

CHUNKS_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "chunks.json"
UUID_NS = uuid.UUID("6f1c0d1e-0000-4000-8000-00000000e7c0")  # ids stables => ré-indexation idempotente


def load_chunks(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_payload(chunk: dict, index: int) -> dict:
    m = chunk["metadata"]
    return {
        "text": chunk["text"],  # texte original, utilisé pour les citations
        "chunk_id": m.get("chunk_id") or f"{m.get('doc_id', '')}#{index}",
        "citation": m.get("citation", ""),
        "section_number": m.get("section_number", ""),
        "part": m.get("part", 1),
        "doc_id": m.get("doc_id", ""),
        "title": m.get("title", ""),
        "doc_type": m.get("doc_type", ""),
        "version": m.get("version", ""),
        "effective_date": m.get("effective_date", ""),
        "section": m.get("section_title", ""),
        "clauses": m.get("clauses", []),
        "source_file": m.get("source_file", ""),
        "language": m.get("language", "fr"),
    }


def index_policies(model_name: str, collection: str, host: str, port: int,
                   qdrant_path: str | None, batch_size: int, chunks_path: Path = CHUNKS_PATH):
    chunks = load_chunks(chunks_path)
    print(f"[INFO] {len(chunks)} chunks chargés depuis {chunks_path}")

    print(f"[INFO] Chargement du modèle : {model_name}")
    model = load_model(model_name)
    dim = model.get_embedding_dimension()

    texts = [build_embedding_text(c) for c in chunks]
    print(f"[INFO] Calcul des embeddings ({len(texts)} textes, dimension {dim})...")
    vectors = embed_documents(model, texts, batch_size=batch_size)

    client = QdrantClient(path=qdrant_path) if qdrant_path else QdrantClient(host=host, port=port)
    if client.collection_exists(collection):
        client.delete_collection(collection)
    client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    points = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        payload = build_payload(chunk, i)
        points.append(PointStruct(
            id=str(uuid.uuid5(UUID_NS, f"{model_name}|{payload['chunk_id']}")),
            vector=vector.tolist(),
            payload=payload,
        ))
    client.upsert(collection_name=collection, points=points)
    print(f"✅ {len(points)} chunks indexés dans '{collection}' (modèle {model_name}, dim {dim})")
    return client


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--collection", default="policies")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=6333)
    ap.add_argument("--qdrant-path", default=None, help="mode local sans serveur Qdrant")
    ap.add_argument("--batch-size", type=int, default=32)
    args = ap.parse_args()
    index_policies(args.model, args.collection, args.host, args.port, args.qdrant_path, args.batch_size)
