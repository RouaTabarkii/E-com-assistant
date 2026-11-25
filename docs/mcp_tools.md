# Outils MCP de l'assistant e-commerce

Trois outils sont exposés à l'agent. Ce document décrit leur **contrat** : paramètres d'entrée, format de sortie et erreurs possibles.

| Outil | Fichier | Rôle |
|---|---|---|
| `run_sql` | `src/mcp_server/run_sql.py` | Exécute une requête SQL en lecture seule sur la base Olist (PostgreSQL). |
| `search_policies` | `src/mcp_server/search_policies.py` | Recherche sémantique de passages dans les politiques de l'entreprise (Qdrant). |
| `explain_schema` | `src/mcp_server/explain_schema.py` | Décrit les tables, colonnes et relations de la base. |

> **État actuel :** les trois outils sont des fonctions Python. Le serveur MCP qui les expose n'est pas encore écrit. Les schémas JSON ci-dessous (`inputSchema`) sont ceux à déclarer lors de l'exposition MCP.

## Convention d'erreurs : point d'attention

Les trois outils ne signalent pas leurs erreurs de la même façon aujourd'hui.

| Outil | Entrée invalide | Erreur d'infrastructure (base, Qdrant) |
|---|---|---|
| `run_sql` | renvoie `{"error": "..."}` | renvoie `{"error": "..."}` |
| `search_policies` | **lève** `ValueError` | **lève** l'exception du client (Qdrant) |
| `explain_schema` | **lève** `ValueError` | **lève** l'exception SQLAlchemy |

Le code appelant (nœuds de l'agent, couche MCP) doit donc gérer les deux cas : tester la clé `error` pour `run_sql`, intercepter les exceptions pour les deux autres. Une harmonisation (par exemple un format d'erreur MCP unique) est à décider lors de l'écriture du serveur.

---

## 1. `run_sql`

Exécute **une** requête `SELECT` ou `WITH` sur la base Olist, avec validation, limite de lignes et délai maximal.

### Entrée

```json
{
  "type": "object",
  "properties": {
    "query": { "type": "string", "description": "Requête SQL SELECT ou WITH (une seule instruction)." },
    "limit": { "type": "integer", "default": 100, "description": "Nombre maximal de lignes, ajouté seulement si la requête n'a pas de LIMIT." }
  },
  "required": ["query"]
}
```

### Sortie (succès)

```json
{
  "columns": ["order_status", "n"],
  "rows": [["delivered", 96478], ["shipped", 1107]],
  "row_count": 2,
  "duration_ms": 41.37,
  "query_executed": "SELECT order_status, COUNT(*) AS n FROM orders GROUP BY 1 LIMIT 100"
}
```

| Champ | Type | Description |
|---|---|---|
| `columns` | `string[]` | Noms des colonnes. |
| `rows` | `any[][]` | Lignes, chaque ligne étant une liste ordonnée comme `columns`. |
| `row_count` | `integer` | Nombre de lignes renvoyées. |
| `duration_ms` | `number` | Durée d'exécution, en millisecondes. |
| `query_executed` | `string` | Requête réellement exécutée (avec le `LIMIT` éventuellement ajouté). C'est elle qu'il faut afficher à l'utilisateur. |

### Sortie (erreur)

```json
{ "error": "Forbidden keyword(s) detected: DROP" }
```

| Message d'erreur | Cause |
|---|---|
| `Only SELECT or WITH queries are allowed.` | La requête ne commence pas par `SELECT` ou `WITH`. |
| `Forbidden keyword(s) detected: X, Y` | Un mot interdit apparaît : `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `ATTACH`, `PRAGMA`, `GRANT`, `REVOKE`, `EXECUTE`, `CALL`. |
| `Multiple statements are not allowed.` | Un `;` apparaît avant la fin de la requête. |
| `Database error: ...` | Erreur d'exécution SQLAlchemy (`OperationalError`) : connexion impossible, délai de 10 s dépassé, etc. |
| `Unexpected error: ...` | Toute autre erreur, par exemple SQL invalide (table ou colonne inconnue). |

### Garde-fous

- Maximum 100 lignes par défaut (`MAX_ROWS`).
- Délai d'exécution de 10 secondes (`statement_timeout`).
- Chaque requête (acceptée, rejetée ou en erreur) est journalisée dans `logs/sql_queries.log`.

### Limites connues

- Le `LIMIT` n'est ajouté que si le mot `LIMIT` est absent de la requête. Un `LIMIT 1000000` écrit par le LLM n'est **pas** plafonné, et la présence du mot dans un littéral ou un nom de colonne désactive aussi l'ajout.
- Le mot-clé interdit est détecté même dans un texte entre guillemets (`WHERE x = 'update'` est rejeté).
- Le paramètre `limit` n'est pas validé (valeur négative ou non entière).
- Le caractère « lecture seule » repose sur la validation du texte. Le commentaire du code suppose un utilisateur PostgreSQL en lecture seule, mais `docker-compose.yml` ne crée que l'utilisateur propriétaire `olistiq` : à vérifier ou à créer.
- Le fichier de log est ouvert à l'import avec un chemin relatif (`logs/sql_queries.log`) : il faut lancer depuis la racine du projet, avec le dossier `logs/` présent.

---

## 2. `search_policies`

Recherche sémantique (embeddings BGE-M3, similarité cosinus) dans la collection Qdrant `policies` et renvoie les passages les plus proches.

### Entrée

```json
{
  "type": "object",
  "properties": {
    "question": { "type": "string", "minLength": 1, "description": "Question en langage naturel (français ou anglais)." },
    "k": { "type": "integer", "minimum": 1, "maximum": 10, "default": 3, "description": "Nombre de passages à renvoyer." },
    "doc_type": { "type": "string", "description": "Filtre exact sur le type de politique." },
    "doc_id": { "type": "string", "description": "Filtre exact sur l'identifiant du document, ex. POL-RET-001." },
    "version": { "type": "string", "description": "Filtre exact sur la version, ex. 2.0." }
  },
  "required": ["question"]
}
```

Les filtres sont facultatifs et **cumulatifs** (ET logique). Valeurs présentes dans le corpus actuel :

| `doc_id` | `doc_type` | `version` |
|---|---|---|
| POL-RET-001 | `retour` | 2.0 |
| POL-REF-002 | `remboursement` | 1.3 |
| POL-DEL-003 | `livraison` | 2.1 |
| POL-WAR-004 | `garantie` | 1.1 |
| POL-SEL-005 | `vendeur` | 1.4 |
| POL-REV-006 | `avis` | 1.0 |
| POL-PAY-007 | `paiement` | 1.2 |
| POL-PRV-008 | `donnees_personnelles` | 1.0 |
| POL-CAN-009 | `annulation` | 1.0 |

### Sortie

Liste de passages, triés par score décroissant. La liste peut être **vide**.

```json
[
  {
    "chunk_id": "POL-RET-001#s2",
    "score": 0.8123,
    "doc_id": "POL-RET-001",
    "title": "Politique de retour et de rétractation",
    "doc_type": "retour",
    "version": "2.0",
    "section": "2. Droit de rétractation",
    "clauses": ["2.1", "2.2", "2.3"],
    "citation": "[POL-RET-001 v2.0, § 2 Droit de rétractation]",
    "text": "2.1 Le client dispose de **7 jours calendaires** à compter de la réception..."
  }
]
```

| Champ | Type | Description |
|---|---|---|
| `chunk_id` | `string` | Identifiant stable du passage (`<doc_id>#s<section>`, avec suffixe `.n` si la section est découpée). |
| `score` | `number` | Similarité cosinus arrondie à 4 décimales. Plus c'est haut, plus c'est proche. Il n'y a **aucun seuil** : des passages peu pertinents sont renvoyés tant qu'il reste de la place dans `k`. |
| `doc_id`, `title`, `doc_type`, `version` | `string` | Métadonnées du document. |
| `section` | `string` | Titre de la section. |
| `clauses` | `string[]` | Numéros de clauses contenus dans le passage. |
| `citation` | `string` | Citation prête à afficher. |
| `text` | `string` | Texte original du passage. |

### Erreurs

| Erreur | Cause |
|---|---|
| `ValueError("La question ne peut pas être vide.")` | `question` n'est pas une chaîne, ou ne contient que des espaces. |
| `ValueError("k doit être un entier entre 1 et 10.")` | `k` n'est pas un entier, ou hors de `[1, 10]`. |
| Exception du client Qdrant | Serveur injoignable, collection `policies` absente, etc. |

Un filtre qui ne correspond à rien (`doc_type="xyz"`) **n'est pas une erreur** : le résultat est `[]`.

### Limites connues

- Le texte des passages vient de documents : il doit être traité comme une **donnée non fiable** par le LLM (protection contre l'injection de prompt).
- Le client Qdrant (`localhost:6333`) et le modèle sont créés à l'import du module, ce qui rend l'import lent et dépendant de Qdrant.

---

## 3. `explain_schema`

Décrit la structure de la base (introspection SQLAlchemy) enrichie de descriptions métier et des jointures utiles. Aucune donnée n'est lue.

### Entrée

```json
{
  "type": "object",
  "properties": {
    "table": { "type": "string", "description": "Nom d'une table. Omis : vue d'ensemble de toute la base." }
  }
}
```

Le nom est nettoyé (espaces retirés, minuscules) puis comparé à la liste réelle des tables : aucune chaîne de l'appelant n'atteint le SQL.

### Sortie sans `table` : vue d'ensemble

```json
{
  "tables": [
    { "name": "orders", "description": "Commandes (une ligne par commande)...", "n_columns": 8 }
  ],
  "relations": [
    {
      "from_table": "orders", "from_columns": ["customer_id"],
      "to_table": "customers", "to_columns": ["customer_id"],
      "kind": "declared"
    }
  ]
}
```

`kind` vaut `declared` (clé étrangère réelle) ou `logical` (jointure utile mais non déclarée, par exemple vers `geolocation`).

### Sortie avec `table` : détail

```json
{
  "table": "orders",
  "description": "Commandes (une ligne par commande)...",
  "columns": [
    {
      "name": "order_status", "type": "TEXT", "nullable": true,
      "primary_key": false, "foreign_key": false,
      "description": "delivered, shipped, canceled, ..."
    }
  ],
  "primary_key": ["order_id"],
  "references": [ { "from_table": "orders", "to_table": "customers", "kind": "declared", "...": "..." } ],
  "referenced_by": [ { "from_table": "order_items", "to_table": "orders", "kind": "declared", "...": "..." } ]
}
```

`description` vaut `""` quand aucune description métier n'existe pour la colonne ou la table.

La fonction `format_schema(info)` convertit ces deux formats en texte compact, plus économe en tokens que le JSON, à destination du LLM.

### Erreurs

| Erreur | Cause |
|---|---|
| `ValueError("Le nom de table ne peut pas être vide.")` | `table` n'est pas une chaîne, ou est vide. |
| `ValueError("Table inconnue : 'x'. Tables disponibles : ...")` | La table n'existe pas ; le message liste les tables valides. |
| Exception SQLAlchemy | Base injoignable. |

### Limite connue

- Les descriptions métier sont écrites à la main dans le code (`TABLE_DESCRIPTIONS`, `COLUMN_DESCRIPTIONS`). Elles ne suivent pas automatiquement un changement du schéma.