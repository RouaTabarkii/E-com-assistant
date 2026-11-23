"""Outil MCP `explain_schema` : décrit les tables, colonnes et relations de la base Olist.

Sert au nœud « génération SQL » de l'agent : avant d'écrire une requête, il demande
la structure réelle de la base (introspection SQLAlchemy) enrichie de descriptions
métier et des jointures utiles.

    python -m src.mcp_server.explain_schema               # vue d'ensemble
    python -m src.mcp_server.explain_schema orders        # détail d'une table
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect

load_dotenv()

# --------------------------------------------------------------------------- #
# Connaissance métier (statique) : la base ne contient pas ces descriptions.
# --------------------------------------------------------------------------- #
TABLE_DESCRIPTIONS = {
    "customers": "Clients. Un customer_id est lié à UNE commande ; customer_unique_id identifie la personne réelle.",
    "orders": "Commandes (une ligne par commande) avec statut et horodatages du cycle de vie.",
    "order_items": "Lignes de commande : un produit vendu par un vendeur dans une commande (prix, frais de port).",
    "order_payments": "Paiements d'une commande (une commande peut avoir plusieurs paiements/échéances).",
    "order_reviews": "Avis clients (note 1-5 + commentaire) sur une commande. review_id n'est pas unique.",
    "products": "Catalogue produits (catégorie en portugais, dimensions, poids).",
    "sellers": "Vendeurs de la marketplace.",
    "geolocation": "Coordonnées par préfixe de code postal (plusieurs lignes par préfixe).",
    "product_category_translation": "Traduction des catégories produits du portugais vers l'anglais.",
}

COLUMN_DESCRIPTIONS = {
    "orders": {
        "order_status": "delivered, shipped, canceled, unavailable, invoiced, processing, created, approved",
        "order_purchase_timestamp": "Date/heure d'achat",
        "order_delivered_customer_date": "Date de livraison réelle (NULL si non livrée)",
        "order_estimated_delivery_date": "Date de livraison promise ; retard = delivered_customer_date > estimated",
    },
    "order_items": {
        "order_item_id": "Numéro de la ligne dans la commande (1, 2, 3…), pas un identifiant global",
        "price": "Prix de l'article (BRL)",
        "freight_value": "Frais de port de la ligne (BRL)",
    },
    "order_payments": {
        "payment_type": "credit_card, boleto, voucher, debit_card",
        "payment_installments": "Nombre d'échéances",
        "payment_value": "Montant payé (BRL)",
    },
    "order_reviews": {"review_score": "Note de 1 à 5"},
    "products": {"product_category_name": "Catégorie en portugais (voir product_category_translation)"},
    "customers": {"customer_unique_id": "Identifiant stable d'une personne (un client peut avoir plusieurs customer_id)"},
}

# Relations « logiques » utiles aux jointures, même si absentes de schema.sql
# (ex. geolocation n'a ni PK ni FK, product_category_name n'est pas déclarée en FK).
LOGICAL_RELATIONS = [
    ("products", ["product_category_name"], "product_category_translation", ["product_category_name"]),
    ("customers", ["customer_zip_code_prefix"], "geolocation", ["geolocation_zip_code_prefix"]),
    ("sellers", ["seller_zip_code_prefix"], "geolocation", ["geolocation_zip_code_prefix"]),
]

_engine = None


def get_engine():
    """Moteur PostgreSQL construit comme dans load_olist.py (variables .env)."""
    global _engine
    if _engine is None:
        url = (
            f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
            f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        )
        _engine = create_engine(url)
    return _engine


def _relations(insp, tables):
    """Relations déclarées (FK réelles) + logiques, dédupliquées."""
    rels, seen = [], set()
    for t in tables:
        for fk in insp.get_foreign_keys(t):
            key = (t, tuple(fk["constrained_columns"]), fk["referred_table"], tuple(fk["referred_columns"]))
            if key not in seen:
                seen.add(key)
                rels.append({"from_table": t, "from_columns": fk["constrained_columns"],
                             "to_table": fk["referred_table"], "to_columns": fk["referred_columns"],
                             "kind": "declared"})
    for t, cols, rt, rcols in LOGICAL_RELATIONS:
        key = (t, tuple(cols), rt, tuple(rcols))
        if key not in seen and t in tables and rt in tables:
            seen.add(key)
            rels.append({"from_table": t, "from_columns": cols, "to_table": rt,
                         "to_columns": rcols, "kind": "logical"})
    return rels


def explain_schema(table=None, engine=None):
    """Décrit le schéma. Sans `table` : vue d'ensemble ; avec `table` : détail d'une table.

    Lecture seule (introspection des métadonnées, aucune donnée lue). Le nom de table est
    validé contre la liste réelle des tables : aucune chaîne de l'appelant n'atteint le SQL.
    """
    insp = inspect(engine or get_engine())
    tables = sorted(insp.get_table_names())
    rels = _relations(insp, tables)

    if table is None:
        return {
            "tables": [{"name": t, "description": TABLE_DESCRIPTIONS.get(t, ""),
                        "n_columns": len(insp.get_columns(t))} for t in tables],
            "relations": rels,
        }

    if not isinstance(table, str) or not table.strip():
        raise ValueError("Le nom de table ne peut pas être vide.")
    wanted = table.strip().lower()
    if wanted not in tables:
        raise ValueError(f"Table inconnue : {table!r}. Tables disponibles : {', '.join(tables)}.")

    pk = set(insp.get_pk_constraint(wanted).get("constrained_columns") or [])
    fk_cols = {c for r in rels if r["from_table"] == wanted for c in r["from_columns"]}
    notes = COLUMN_DESCRIPTIONS.get(wanted, {})
    return {
        "table": wanted,
        "description": TABLE_DESCRIPTIONS.get(wanted, ""),
        "columns": [{
            "name": c["name"], "type": str(c["type"]), "nullable": c["nullable"],
            "primary_key": c["name"] in pk, "foreign_key": c["name"] in fk_cols,
            "description": notes.get(c["name"], ""),
        } for c in insp.get_columns(wanted)],
        "primary_key": sorted(pk),
        "references": [r for r in rels if r["from_table"] == wanted],
        "referenced_by": [r for r in rels if r["to_table"] == wanted],
    }


def _fmt(r):
    return (f"{r['from_table']}({', '.join(r['from_columns'])}) -> "
            f"{r['to_table']}({', '.join(r['to_columns'])})  [{r['kind']}]")


def format_schema(info):
    """Texte compact destiné au LLM (moins de tokens que le JSON)."""
    if "tables" in info:
        lines = ["TABLES :"] + [f"- {t['name']} ({t['n_columns']} col.) : {t['description']}" for t in info["tables"]]
        lines += ["", "RELATIONS (jointures) :"] + [f"- {_fmt(r)}" for r in info["relations"]]
        return "\n".join(lines)
    lines = [f"TABLE {info['table']} : {info['description']}",
             f"Clé primaire : {', '.join(info['primary_key']) or '(aucune)'}", "COLONNES :"]
    for c in info["columns"]:
        flags = ("PK " if c["primary_key"] else "") + ("FK " if c["foreign_key"] else "")
        extra = f" — {c['description']}" if c["description"] else ""
        lines.append(f"- {c['name']} {c['type']}{'' if c['nullable'] else ' NOT NULL'} {flags}".rstrip() + extra)
    if info["references"]:
        lines += ["RÉFÉRENCE :"] + [f"- {_fmt(r)}" for r in info["references"]]
    if info["referenced_by"]:
        lines += ["RÉFÉRENCÉE PAR :"] + [f"- {_fmt(r)}" for r in info["referenced_by"]]
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    print(format_schema(explain_schema(sys.argv[1] if len(sys.argv) > 1 else None)))
