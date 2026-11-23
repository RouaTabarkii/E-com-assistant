"""Test rapide de la récupération : le bon document remonte-t-il dans le top-k ?

    python src/evaluation/retrieval_smoke_test.py                       # bge-m3, collection `policies`
    python src/evaluation/retrieval_smoke_test.py --model intfloat/multilingual-e5-base --collection policies_e5

Ce n'est PAS le benchmark final (50 questions, Ragas…) : c'est un contrôle de bon sens
pour vérifier que l'indexation fonctionne et comparer rapidement deux modèles.
Chaque question liste le(s) document(s) acceptables et la clause qui contient la réponse.
"""
import argparse
import sys
from pathlib import Path

from qdrant_client import QdrantClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingestion"))
from embeddings import DEFAULT_MODEL, embed_queries, load_model  # noqa: E402

# (question, [doc_id acceptables], clause de référence)
QUESTIONS = [
    ("Combien de jours ai-je pour me rétracter après réception du produit ?", ["POL-RET-001"], "2.1"),
    ("Who pays the return shipping when I withdraw within 7 days?", ["POL-RET-001"], "3.3"),
    ("Sous combien de temps suis-je remboursé après la validation de mon retour ?", ["POL-REF-002"], "2.1"),
    ("Comment suis-je remboursé si j'ai payé par boleto ?", ["POL-REF-002"], "4.3"),
    ("Que reçoit le client si sa commande arrive avec plus de 15 jours de retard ?", ["POL-DEL-003"], "3.3"),
    ("À partir de quand un colis est-il considéré comme perdu ?", ["POL-DEL-003"], "4.1"),
    ("Quel est le délai de garantie pour un produit durable défectueux ?", ["POL-WAR-004"], "1.2"),
    ("Quelle commission la plateforme prélève-t-elle sur les ventes des vendeurs ?", ["POL-SEL-005"], "2.1"),
    ("Après combien de manquements un vendeur est-il suspendu ?", ["POL-SEL-005"], "5.2"),
    ("Quels types d'avis clients sont supprimés par la modération ?", ["POL-REV-006"], "3.1"),
    ("Combien d'échéances maximum pour un paiement par carte de crédit ?", ["POL-PAY-007"], "2.1"),
    ("How long is a boleto valid before the order is cancelled?", ["POL-PAY-007", "POL-CAN-009"], "3.1"),
    ("Pendant combien d'années conservez-vous mes données de commande ?", ["POL-PRV-008"], "3.1"),
    ("Puis-je annuler ma commande une fois qu'elle est expédiée ?", ["POL-CAN-009"], "2.1"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--collection", default="policies")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=6333)
    ap.add_argument("--qdrant-path", default=None)
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()

    model = load_model(args.model)
    client = QdrantClient(path=args.qdrant_path) if args.qdrant_path else QdrantClient(host=args.host, port=args.port)
    vectors = embed_queries(model, [q for q, _, _ in QUESTIONS])

    hits_at = {1: 0, 3: 0, args.k: 0}
    rr_sum = 0.0
    for (question, accepted, clause), vec in zip(QUESTIONS, vectors):
        res = client.query_points(args.collection, query=vec.tolist(), limit=args.k, with_payload=True).points
        ranked = [(p.payload["doc_id"], p.payload["section"], p.score) for p in res]
        rank = next((i + 1 for i, (d, _, _) in enumerate(ranked) if d in accepted), None)
        for k in hits_at:
            if rank and rank <= k:
                hits_at[k] += 1
        rr_sum += 1 / rank if rank else 0.0
        mark = "OK " if rank == 1 else ("~  " if rank else "KO ")
        top = ranked[0]
        print(f"{mark} rang={rank or '-'}  attendu={'/'.join(accepted)} §{clause}  |  top1={top[0]} « {top[1]} » ({top[2]:.2f})")
        if not rank or rank > 1:
            print(f"      Q: {question}")

    n = len(QUESTIONS)
    print("\n" + "=" * 60)
    print(f"Modèle {args.model} | collection {args.collection} | {n} questions")
    for k, v in sorted(hits_at.items()):
        print(f"  Recall@{k}: {v}/{n} = {v / n:.0%}")
    print(f"  MRR: {rr_sum / n:.3f}")


if __name__ == "__main__":
    main()
