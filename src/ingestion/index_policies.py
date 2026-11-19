import json
import uuid
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct
)
from sentence_transformers import SentenceTransformer

# --- Config ---
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "policies"
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
CHUNKS_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "chunks.json"

def load_chunks(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def index_policies():
    # Load chunks
    chunks = load_chunks(CHUNKS_PATH)
    print(f"[INFO] {len(chunks)} chunks loaded")

    # Load embedding model
    print(f"[INFO] Loading model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Connect to Qdrant
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # Create collection (drop if exists)
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=model.get_sentence_embedding_dimension(),
            distance=Distance.COSINE,
        ),
    )
    print(f"[INFO] Collection '{COLLECTION_NAME}' created")

    # Embed + index in batches
    BATCH_SIZE = 64
    points = []

    texts = [chunk["text"] for chunk in chunks]
    print(f"[INFO] Embedding {len(texts)} chunks...")
    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector.tolist(),
                payload={
                    "text":          chunk["text"],
                    "doc_id":        chunk["metadata"].get("doc_id", ""),
                    "title":         chunk["metadata"].get("title", ""),
                    "doc_type":      chunk["metadata"].get("doc_type", ""),
                    "version":       chunk["metadata"].get("version", ""),
                    "effective_date":chunk["metadata"].get("effective_date", ""),
                    "section":       chunk["metadata"].get("section_title", ""),
                    "source_file":   chunk["metadata"].get("source_file", ""),
                    "language":      chunk["metadata"].get("language", "fr"),
                    "chunk_id":      i,
                },
            )
        )

    # Upload to Qdrant
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"\n✅ {len(points)} chunks indexed into Qdrant collection '{COLLECTION_NAME}'")

if __name__ == "__main__":
    index_policies()