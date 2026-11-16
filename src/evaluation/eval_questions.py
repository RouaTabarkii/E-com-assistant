import csv
from pathlib import Path

REPARTITION = [
    ("donnees",       "sql",          20),
    ("politique",     "docs",         20),
    ("hybride",       "both",          10),

]

COLONNES = [
    "id", "type", "question", "voie_attendue",
    "sql_reference", "passages_reference", "reponse_attendue", "notes",
]

OUT = Path("data/eval/eval_questions.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=COLONNES)
    writer.writeheader()
    n = 1
    for type_q, voie, nombre in REPARTITION:
        for _ in range(nombre):
            writer.writerow({"id": f"Q-{n:03d}", "type": type_q, "voie_attendue": voie})
            n += 1


