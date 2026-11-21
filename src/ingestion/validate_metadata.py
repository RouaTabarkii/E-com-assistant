"""Contrôle qualité des métadonnées de chaque passage (à lancer entre chunking et indexation).

    python src/ingestion/validate_metadata.py

Vérifie sur data/processed/chunks.json :
  - tous les champs obligatoires sont présents et non vides ;
  - chunk_id unique ;
  - version / date au bon format ;
  - doc_id, version et doc_type identiques à ceux de data/policies/corpus_index.csv ;
  - chaque passage de politique contient au moins une clause numérotée (citation possible).
Code de sortie 1 s'il y a au moins une erreur (utilisable en CI).
"""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHUNKS = ROOT / "data" / "processed" / "chunks.json"
INDEX = ROOT / "data" / "policies" / "corpus_index.csv"

REQUIRED = ["doc_id", "title", "doc_type", "version", "effective_date", "language",
            "source_file", "section_title", "section_number", "chunk_id", "citation"]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VERSION_RE = re.compile(r"^\d+(\.\d+)*$")
ALLOWED_LANG = {"fr", "en"}


def main() -> int:
    chunks = json.loads(CHUNKS.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []

    reference = {}
    if INDEX.exists():
        with open(INDEX, encoding="utf-8", newline="") as f:
            reference = {r["doc_id"]: r for r in csv.DictReader(f)}
    else:
        warnings.append(f"{INDEX.name} introuvable : comparaison avec l'index ignorée")

    ids = Counter(c["metadata"].get("chunk_id") for c in chunks)
    for cid, n in ids.items():
        if n > 1:
            errors.append(f"chunk_id en double ({n}x) : {cid}")

    for c in chunks:
        m = c["metadata"]
        where = m.get("chunk_id", "<sans chunk_id>")

        for field in REQUIRED:
            if not str(m.get(field, "")).strip():
                errors.append(f"{where} : champ manquant ou vide « {field} »")

        if m.get("version") and not VERSION_RE.match(str(m["version"])):
            errors.append(f"{where} : version invalide « {m['version']} »")
        if m.get("effective_date") and not DATE_RE.match(str(m["effective_date"])):
            errors.append(f"{where} : date invalide « {m['effective_date']} » (attendu AAAA-MM-JJ)")
        if m.get("language") and m["language"] not in ALLOWED_LANG:
            errors.append(f"{where} : langue inattendue « {m['language']} »")
        if not c["text"].strip():
            errors.append(f"{where} : texte vide")

        if m.get("file_type") == "md" and not m.get("clauses"):
            warnings.append(f"{where} : aucune clause numérotée détectée (citation moins précise)")

        ref = reference.get(m.get("doc_id"))
        if reference and ref is None:
            errors.append(f"{where} : doc_id absent de corpus_index.csv")
        elif ref:
            for field in ("version", "doc_type", "effective_date"):
                if str(m.get(field)) != ref[field]:
                    errors.append(f"{where} : {field} « {m.get(field)} » ≠ index « {ref[field]} »")

    # Documents de l'index qui n'ont produit aucun passage
    for doc_id in reference:
        if not any(c["metadata"].get("doc_id") == doc_id for c in chunks):
            errors.append(f"{doc_id} : présent dans corpus_index.csv mais aucun passage indexé")

    docs = Counter(c["metadata"].get("doc_id") for c in chunks)
    print(f"{len(chunks)} passages, {len(docs)} documents")
    for doc_id, n in sorted(docs.items()):
        print(f"  {doc_id}: {n} passages")
    for w in warnings:
        print(f"[WARN] {w}")
    for e in errors:
        print(f"[ERREUR] {e}")
    print("\n✅ Métadonnées valides" if not errors else f"\n❌ {len(errors)} erreur(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
