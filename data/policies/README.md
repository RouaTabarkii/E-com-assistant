# Corpus de politiques — documentation

## Description
Corpus de 9 documents de politiques **fictifs** rédigés pour le projet, cohérents avec l'univers
du jeu de données Olist (marketplace brésilienne, montants en BRL, statuts de commande et
moyens de paiement identiques à ceux de la base). Les règles s'inspirent du cadre général du droit
de la consommation brésilien (délai de rétractation de 7 jours, garanties de 30 et 90 jours) mais
ne constituent pas des documents juridiques réels.

## Liste des documents
Voir `corpus_index.csv` (une ligne par document, avec métadonnées et documents liés).

## Format d'un document
- Fichier Markdown, nom `POL-<TYPE>-<NNN>_<slug>.md`.
- En-tête YAML : `doc_id`, `title`, `doc_type`, `version`, `effective_date`, `language`, `owner`.
- Corps structuré en sections numérotées (`## 1.`) et clauses numérotées (`1.1`, `1.2`…).
  Les numéros de clause servent de **cible de citation** : `[POL-DEL-003, § 3.2]`.

## Schéma de métadonnées pour l'indexation
| Champ | Source | Usage |
|---|---|---|
| `doc_id` | en-tête YAML | identifiant, citation |
| `title` | en-tête YAML | affichage |
| `doc_type` | en-tête YAML | filtre de recherche |
| `version` | en-tête YAML | filtre / traçabilité |
| `effective_date` | en-tête YAML | filtre de validité |
| `language` | en-tête YAML | filtre |
| `section` | titre `##` du chunk | citation |
| `clause` | numéros de clause couverts par le chunk | citation précise |
| `chunk_id` | généré (`doc_id#section`) | identifiant du passage |
| `source_path` | chemin du fichier | lien vers la source |

## Consignes de découpage recommandées
- Un chunk = une section `##` (les sections sont courtes). Si une section dépasse ~400 tokens,
  la couper par clause en gardant le titre de section en préfixe.
- Conserver le titre du document et de la section dans le texte du chunk pour aider la recherche.

## Liens utiles avec la base de données (questions hybrides)
- Retard de livraison : `order_delivered_customer_date` > `order_estimated_delivery_date`
  (POL-DEL-003 : paliers de 7 et 15 jours).
- Statuts de commande : `orders.order_status` (POL-DEL-003 § 2, POL-CAN-009).
- Moyens de paiement : `order_payments.payment_type`, `payment_installments` (POL-PAY-007).
- Notes : `order_reviews.review_score` de 1 à 5 (POL-REV-006, POL-SEL-005).

## Règles de maintenance
- Toute modification d'un document incrémente `version` et met à jour `corpus_index.csv`.
- Ne pas renuméroter les clauses existantes : les jeux de test y font référence.
