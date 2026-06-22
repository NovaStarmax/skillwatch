# SkillWatch — Pipeline d'Agrégation (C3)

## Objectif

Décrire l'algorithme de nettoyage et normalisation qui transforme des données brutes hétérogènes en
un référentiel unifié de compétences tech.

## Dépendances

| Dépendance | Version | Rôle |
|-----------|---------|------|
| pandas | latest | Lecture CSV Stack Overflow |
| pyspark | 3.5.0 | Traitement archives multi-années |
| playwright | >=1.60.0 | Scraping JavaScript OpenClassrooms |
| beautifulsoup4 | latest | Parsing HTML |
| sqlalchemy | latest | Connexions PostgreSQL |
| requests | latest | Appels API France Travail |

## Commandes

```bash
just pipeline          # Lance le pipeline complet
just extract-france    # France Travail uniquement
just extract-spark     # Spark uniquement
just transform         # Recalcule market_summary
```

## Algorithme de normalisation

Le problème central : les mêmes compétences apparaissent sous des formes différentes selon la
source.

Exemples :
- France Travail : "Python (langage de programmation)"
- Stack Overflow : "Python"
- OpenClassrooms : "Langage Python, Pandas, Sk-Learn"

### Étape 1 — Tokenisation

Le texte brut est découpé en tokens :

```python
tokens = set(re.split(r'[\s\-/;,.()\[\]]+', texte.lower()))
```

Pour les valeurs multi-valeurs Stack Overflow (séparées par ";") :

```python
tokens = {t.strip().lower() for t in valeur.split(";")}
```

### Étape 2 — Lookup dans le mapping

Chaque token est comparé au dictionnaire `config/skills_mapping.json` :

```python
if alias in tokens:
    canonical = mapping[alias]  # ex: "python" → "Python"
```

Règle pour les aliases multi-mots ("spring boot", "node.js") : substring match plutôt que token
exact.

### Étape 3 — Normalisation vers le canonique

Le nom canonique est inséré dans la table `skills` avec ON CONFLICT DO NOTHING :

```sql
INSERT INTO skills (name, category)
VALUES (:name, 'unknown')
ON CONFLICT (name) DO NOTHING
```

### Étape 4 — Traçabilité des non-matchés

Les valeurs non reconnues sont loggées par source :

```
data/logs/unmatched_france_travail.log
data/logs/unmatched_stackoverflow.log
data/logs/unmatched_openclassrooms.log
data/logs/unmatched_spark.log
```

Format :

```
[UNMATCHED] source: france_travail | offre: 209RZSH | title: Data Engineer
```

### Étape 5 — Enrichissement itératif

Le fichier `config/skills_mapping.json` est enrichi manuellement entre les runs selon les logs.
Chaque enrichissement est committé dans Git avec un message explicite :

```
feat: enrich skills mapping — add langchain, polars, dbt
```

L'historique Git constitue la trace documentée du processus de normalisation.

## Calcul de market_summary

Après extraction, `just transform` calcule une ligne synthétique par skill :

```python
job_offer_count       = COUNT offres France Travail
developer_usage_count = usage_count Stack Overflow 2025
avg_salary_eur        = avg_salary_usd × 0.92
training_count        = COUNT formations OpenClassrooms
top_dept              = département avec le plus d'offres
```

## Choix de nettoyage documentés

| Décision | Justification |
|----------|---------------|
| Aliases courts supprimés ("c", "r", "go") | Trop ambigus, faux positifs sur texte FR |
| Matching hybride token/substring | Préserve les aliases multi-mots |
| NULL pour salary si absent | Préférable à une moyenne fausse |
| Filtre domaine OpenClassrooms | Formations non-tech hors périmètre |
| Taux fixe USD→EUR (0.92) | Projet analytique, pas financier |
