# SkillWatch — Requêtes SQL Documentées

## Introduction

SkillWatch croise trois sources de données (France Travail, Stack Overflow, OpenClassrooms) pour
répondre aux besoins de veille compétences de l'OTCM. Ces requêtes constituent le cœur analytique
du pipeline et de l'API : elles couvrent la demande marché, les niveaux de rémunération, la
distribution géographique et l'évolution temporelle des compétences Data & IA.

---

## Requête 1 — Offres d'emploi demandant Python

**Contexte métier :**
"En tant que recruteur, je veux voir toutes les offres qui demandent Python."

```sql
SELECT jo.title, jo.company, jo.location,
       jo.salary_min, jo.salary_max
FROM job_offers jo
JOIN job_offer_skills jos ON jo.id = jos.job_offer_id
JOIN skills s ON s.id = jos.skill_id
WHERE s.name = 'Python'
  AND jo.salary_min IS NOT NULL
ORDER BY jo.salary_min DESC
LIMIT 10;
```

**Explication :**

- **JOIN × 2** : la table `job_offer_skills` est une table d'association (N-N) entre `job_offers`
  et `skills`. Sans elle, il est impossible de relier une offre à ses compétences.
- **WHERE s.name = 'Python'** : filtre sur la compétence cible. Seules les offres liées à Python
  remontent.
- **AND jo.salary_min IS NOT NULL** : exclut les offres sans fourchette salariale pour ne présenter
  que des résultats exploitables.
- **ORDER BY salary_min DESC** : les offres les mieux rémunérées en bas de fourchette apparaissent
  en premier — critère plus fiable que salary_max qui peut être gonflé.

**Résultats obtenus :**

| Titre | Entreprise | Localisation | Salaire min | Salaire max |
|-------|-----------|-------------|------------|------------|
| Directeur Data & Intelligence Artificielle (F/H) | NEXTGEN RH | 75 - Paris | 75 000 | 90 000 |
| Senior Full Stack Engineer - Python & IA (H/F) | TALENT BRUT RECRUTEMENT | 75 - PARIS | 70 000 | 100 000 |
| Architecte Data GCP & AWS H/F | JEMS | 34 - Montpellier | 65 000 | 80 000 |
| Consultant.e Data Engineer Microsoft Fabric F/H | Valoway | 75 - Paris | 60 000 | 70 000 |
| Senior Data Engineer – IA & Architectures Avancées H/F | Mercato de l'emploi | 67 - Strasbourg | 60 000 | 70 000 |

---

## Requête 2 — Top 10 skills les plus demandés

**Contexte métier :**
"Quelles sont les compétences les plus recherchées sur le marché français ?"

```sql
SELECT s.name, s.category,
       COUNT(DISTINCT jos.job_offer_id) as nb_offres
FROM skills s
JOIN job_offer_skills jos ON s.id = jos.skill_id
GROUP BY s.name, s.category
ORDER BY nb_offres DESC
LIMIT 10;
```

**Explication :**

- **COUNT(DISTINCT jos.job_offer_id)** : on compte les offres distinctes par compétence et non les
  lignes de la table d'association. Sans `DISTINCT`, une offre citant Python deux fois serait
  comptée deux fois, ce qui fausserait le classement.
- **GROUP BY s.name, s.category** : on regroupe sur les deux colonnes car `category` n'est pas
  fonctionnellement dépendant de `name` au sens SQL strict — PostgreSQL l'exige dans le `SELECT`.
  En pratique, chaque skill a une seule catégorie ; le double `GROUP BY` ne crée pas de doublons.

**Résultats obtenus :**

| Compétence | Catégorie | Nb offres |
|-----------|----------|----------|
| Python | language | 274 |
| SQL | language | 216 |
| Azure | cloud | 111 |
| Git | tool | 93 |
| GCP | cloud | 88 |
| AWS | cloud | 86 |
| Power BI | tool | 86 |
| Java | language | 72 |
| Docker | devops | 71 |
| Spark | bigdata | 69 |

**Lecture :** Python domine avec 274 offres, soit 27 % de plus que SQL (2e). Les clouds (Azure, GCP,
AWS) occupent 3 des 8 places suivantes, signe que la maîtrise d'un hyperscaler est devenue
incontournable.

---

## Requête 3 — Skills les mieux rémunérés

**Contexte métier :**
"Quelles compétences sont associées aux meilleurs salaires dans les offres françaises ?"

```sql
SELECT s.name,
       COUNT(jo.id) as nb_offres,
       ROUND(AVG((jo.salary_min + jo.salary_max) / 2.0)) as salaire_moyen_eur
FROM skills s
JOIN job_offer_skills jos ON s.id = jos.skill_id
JOIN job_offers jo ON jos.job_offer_id = jo.id
WHERE jo.salary_min IS NOT NULL
  AND jo.salary_max IS NOT NULL
GROUP BY s.name
HAVING COUNT(jo.id) >= 3
ORDER BY salaire_moyen_eur DESC
LIMIT 10;
```

**Explication :**

- **(salary_min + salary_max) / 2** : les offres France Travail publient une fourchette et non un
  salaire fixe. Le point médian est la meilleure approximation du salaire réel sans sur-pondérer
  l'un des extrêmes.
- **HAVING COUNT(jo.id) >= 3** : filtre les compétences anecdotiques. Sans ce garde-fou, une
  compétence présente dans une seule offre très bien payée remonterait en tête et biaiserait
  l'analyse.
- **WHERE vs HAVING** : `WHERE` filtre les lignes *avant* agrégation (ici : on exclut les offres
  sans fourchette salariale) ; `HAVING` filtre les groupes *après* agrégation (ici : on exclut les
  skills avec moins de 3 offres). Les deux ne sont pas interchangeables.

**Résultats obtenus :**

| Compétence | Nb offres | Salaire moyen (€) |
|-----------|----------|------------------|
| Looker Studio | 7 | 53 214 |
| Snowflake | 10 | 52 500 |
| Spark | 20 | 52 500 |
| SAS | 3 | 52 167 |
| Kafka | 6 | 51 500 |
| FastAPI | 6 | 51 125 |
| SonarQube | 3 | 50 000 |
| Databricks | 14 | 50 000 |
| GCP | 20 | 49 825 |
| Azure | 35 | 49 652 |

---

## Requête 4 — Offres par département avec ratio démographique

**Contexte métier :**
"Quels départements concentrent le plus d'offres Data par rapport à leur population ?"

```sql
SELECT dept_code,
       location,
       dept_population,
       COUNT(*) as nb_offres,
       ROUND(COUNT(*) * 1000000.0 / dept_population, 1)
           as offres_par_million_hab
FROM job_offers
WHERE dept_population IS NOT NULL
GROUP BY dept_code, location, dept_population
ORDER BY nb_offres DESC
LIMIT 10;
```

**Explication :**

- **Multiplication par 1 000 000** : normaliser par habitant donne un ratio trop petit (ex : 0,000023
  offre/hab). Multiplier par 1 million produit un indice lisible — "23,6 offres pour 1 million
  d'habitants" — comparable entre départements de tailles très différentes.
- **Ratio vs nombre brut** : Paris (75) totalise 63 offres en volume absolu, mais Nantes (44)
  affiche 12,5 offres/million contre 23,6 pour Paris — l'écart se réduit nettement. Le ratio
  révèle que la concentration data n'est pas uniquement parisienne.
- **Jointure cross-DB** : la colonne `dept_population` provient de `demographics_db` (PostgreSQL
  INSEE). L'enrichissement est réalisé en Python lors de l'étape de transformation : les données
  démographiques sont jointes côté applicatif puis stockées directement dans `job_offers`, évitant
  un `dblink` ou une vue fédérée en prod.

**Résultats obtenus :**

| Dept | Localisation | Population | Nb offres | Offres/million hab |
|------|------------|-----------|----------|-------------------|
| 75 | 75 - Paris | 2 119 412 | 50 | 23,6 |
| 92 | 92 - Nanterre | 1 670 575 | 25 | 15,0 |
| 44 | 44 - Nantes | 1 517 043 | 19 | 12,5 |
| 92 | 92 - Levallois-Perret | 1 670 575 | 17 | 10,2 |
| 31 | 31 - Toulouse | 1 494 734 | 15 | 10,0 |
| 75 | 75 - PARIS | 2 119 412 | 13 | 6,1 |
| 59 | 59 - Lille | 2 645 946 | 10 | 3,8 |
| 59 | 59 - Villeneuve-d'Ascq | 2 645 946 | 10 | 3,8 |
| 33 | 33 - Bordeaux | 1 716 986 | 9 | 5,2 |
| 75 | 75 - Paris 12e | 2 119 412 | 9 | 4,2 |

---

## Requête 5 — Évolution de Python sur 5 ans (données Spark)

**Contexte métier :**
"Comment la popularité de Python a-t-elle évolué chez les développeurs de 2021 à 2025 ?"

```sql
SELECT ss.year,
       ss.usage_count,
       ROUND(ss.avg_salary_usd) as salaire_moyen_usd
FROM survey_stats ss
JOIN skills s ON ss.skill_id = s.id
WHERE s.name = 'Python'
ORDER BY ss.year;
```

**Explication :**

- **Source des données** : les archives Stack Overflow Developer Survey 2021–2024 (fichiers CSV
  compressés, plusieurs centaines de Mo) sont traitées via Apache Spark 3.5. Spark permet de lire
  et agréger ces archives en parallèle sans charger l'intégralité en mémoire. L'édition 2025 est
  intégrée via un CSV standard. Les résultats agrégés (`usage_count`, `avg_salary_usd` par skill et
  par année) sont ensuite chargés dans `survey_stats` sur le warehouse PostgreSQL.
- **Lecture year over year** : le pic de 2023 (43 158 utilisateurs déclarés) suivi d'une baisse en
  2024 (30 719) reflète la restructuration du panel Stack Overflow après changement de méthodologie,
  pas un déclin réel de Python. La colonne `usage_count` est donc à lire en tendance relative.
- **Argument Big Data** : sans Spark, traiter 4 années d'archives (>500 Mo au total) en mémoire
  avec pandas provoquerait des OOM sur un VPS standard. Spark distribue le calcul et produit des
  agrégats stables, justifiant son inclusion dans la stack.

**Résultats obtenus :**

| Année | Utilisateurs déclarés | Salaire moyen (USD) |
|------|---------------------|-------------------|
| 2021 | 39 792 | 124 534 |
| 2022 | 34 155 | 190 757 |
| 2023 | 43 158 | 109 211 |
| 2024 | 30 719 | 88 970 |
| 2025 | 18 410 | 100 115 |

---

## Optimisations appliquées

### Index UNIQUE comme mécanisme d'optimisation

Le schéma utilise des contraintes UNIQUE qui créent implicitement des index B-tree dans PostgreSQL :

| Table | Contrainte UNIQUE | Impact |
|-------|------------------|--------|
| skills | name | Lookup O(log n) sur le nom canonique |
| job_offers | external_id | Détection doublons O(log n) à l'upsert |
| survey_stats | (skill_id, year) | Unicité garantie sans scan complet |
| market_summary | skill_id | Accès direct O(log n) par skill |
| trainings | url | Déduplication O(log n) à l'upsert |

### ON CONFLICT — upsert atomique

Le pattern `ON CONFLICT DO UPDATE` évite deux opérations séparées (SELECT + INSERT ou UPDATE) :

```sql
INSERT INTO skills (name, category)
VALUES (:name, :category)
ON CONFLICT (name) DO NOTHING;
```

Une seule opération atomique au lieu de deux. Critique pour un pipeline replayable sans doublons.

### LIMIT sur les endpoints API

Toutes les routes API appliquent un `LIMIT` explicite pour éviter les full scans sur des tables de
300+ skills et 550+ offres. Valeur par défaut : 50.

---

## Synthèse

| Requête | Opérations SQL | Source |
|---------|---------------|--------|
| 1 — Offres Python avec salaire | JOIN × 2, WHERE, ORDER BY | job_offers + skills |
| 2 — Top 10 skills demandés | JOIN, COUNT DISTINCT, GROUP BY | skills + job_offer_skills |
| 3 — Skills les mieux rémunérés | JOIN × 2, AVG, HAVING | job_offers + skills |
| 4 — Offres par département | COUNT, GROUP BY, calcul ratio | job_offers (enrichi INSEE) |
| 5 — Évolution Python 2021–2025 | JOIN, WHERE, ORDER BY | survey_stats (agrégé Spark) |
