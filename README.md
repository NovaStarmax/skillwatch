# SkillWatch — Observatoire du Marché de l'Emploi Data & IA

SkillWatch agrège des données issues de 5 sources hétérogènes pour répondre à une question :
**quelles compétences tech sont demandées, populaires et bien rémunérées en France ?**

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    EXTRACT                          │
│  France Travail API  ·  Stack Overflow CSV (Spark)  │
│  OpenClassrooms (Playwright)                        │
│  → écriture brute dans skillwatch_warehouse.raw.*   │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              TRANSFORM (dbt_skillwatch)             │
│  staging → intermediate → marts                     │
│  seeds : departments (INSEE) · skills_categories    │
│  · skills_mapping                                   │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
        skillwatch_warehouse (5432, un seul Postgres)
        raw · public (seeds) · marts · app (auth)
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                     API REST                        │
│  FastAPI · JWT · /docs (Swagger)  :8000             │
└─────────────────────────────────────────────────────┘
```

## Sources de données

| Source | Méthode | Contenu |
|--------|---------|---------|
| France Travail | API REST (OAuth2) | Offres d'emploi tech en temps réel |
| Stack Overflow | Archives CSV traitées via Apache Spark | Enquêtes développeurs 2021–2025 |
| OpenClassrooms | Scraping Playwright | ~80 parcours de formation tech |
| INSEE | Seed dbt (`departments.csv`) | Population par département |

---

## Prérequis

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — gestionnaire de paquets
- [just](https://just.systems/) — task runner
- Docker + Docker Compose
- Clés API France Travail (Client ID / Client Secret)

---

## Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/NovaStarmax/skillwatch.git
cd skillwatch

# 2. Configurer les variables d'environnement
cp .env.example .env
# Renseigner FRANCE_TRAVAIL_CLIENT_ID, FRANCE_TRAVAIL_CLIENT_SECRET,
# JWT_SECRET_KEY dans .env

# 3. Installer les dépendances Python
uv sync

# 4. Installer Playwright (scraping OpenClassrooms)
uv run playwright install chromium

# 5. Démarrer PostgreSQL
docker compose up -d postgres_warehouse

# 6. Initialiser skillwatch_warehouse (schémas raw/app + seeds dbt)
just db-init

# 7. Lancer l'extraction (raw layer)
just extract
just extract-france-skills  # matching skills France Travail, après extract-france

# 8. Transformer avec dbt (staging → intermediate → marts)
just transform

# 9. Démarrer l'API
just api
# → http://localhost:8000
# → http://localhost:8000/docs
```

Note : l'API tourne en local via just api.
Docker gère uniquement PostgreSQL. Spark (`stackoverflow_spark.py`) tourne en local[*]
dans le process Python, sans conteneur dédié.

---

## Configuration

Copier `.env.example` → `.env` et renseigner :

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | URL PostgreSQL legacy (skillwatch_db, port 5432) — conservée le temps du décommissionnement complet, plus utilisée par le code applicatif |
| `WAREHOUSE_DATABASE_URL` | URL PostgreSQL warehouse (skillwatch_warehouse, port 5432) — raw/staging/marts dbt + `app.users` (auth) |
| `FRANCE_TRAVAIL_CLIENT_ID` | Client ID API France Travail |
| `FRANCE_TRAVAIL_CLIENT_SECRET` | Client Secret API France Travail |
| `JWT_SECRET_KEY` | Clé secrète pour la signature des tokens JWT |
| `ADMIN_USERNAME` | Identifiant administrateur API (défaut : `admin`) |
| `ADMIN_PASSWORD` | Mot de passe administrateur API |

---

## Pipeline ETL/ELT

```bash
# Extraire toutes les sources (raw layer, skillwatch_warehouse.raw.*)
just extract

# Extraire une source spécifique
just extract-france        # France Travail
just extract-france-skills # Matching skills France Travail (après extract-france, avant dbt)
just extract-stackoverflow # Stack Overflow (CSV)
just extract-spark         # Stack Overflow (Spark)
just extract-scraping      # OpenClassrooms

# Transformer les données (dbt : staging → intermediate → marts)
just transform

# Charger uniquement les seeds (departments, skills_categories, skills_mapping)
just dbt-seed

# Simuler l'extraction sans exécution
uv run main.py --dry-run
```

`just pipeline` (`uv run main.py`) n'exécute que l'extraction — la transformation est
désormais entièrement portée par dbt (`just transform`), un outil séparé de `main.py`.

> **Note provisoire (sera réécrite au chapitre 8)** — sur `refacto/dbt-airflow`, le matching
> skills de France Travail a été extrait dans un script Python séparé et rejouable,
> `src/extract/match_skills_france_travail.py` (`just extract-france-skills`), car ce
> matching texte libre n'est pas adapté à du SQL. Il doit tourner **après**
> `just extract-france` et **avant** `dbt run`/`dbt build` : il alimente
> `raw_france_travail_skills_matched`, dont dépend le mart `job_offer_skills`. Cet
> enchaînement n'est pas encore automatisé (pas de DAG Airflow à ce stade) — à exécuter
> manuellement dans cet ordre.

---

## API

```bash
# Démarrer l'API
just api
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
# → http://localhost:8000/redoc (ReDoc)
```

### Authentification

```bash
# 1. Obtenir un token JWT (valable 30 minutes)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "<ADMIN_PASSWORD>"}'

# 2. Utiliser le token
curl http://localhost:8000/skills \
  -H "Authorization: Bearer <token>"
```

### Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/auth/login` | Obtenir un token JWT |
| `GET` | `/health` | État du service |
| `GET` | `/skills` | Liste tous les skills avec statistiques |
| `GET` | `/skills/{name}` | Détail d'un skill |
| `GET` | `/market/summary` | Top 20 skills du marché |
| `GET` | `/market/by-department` | Offres par département (ratio /million hab.) |
| `GET` | `/jobs` | Offres d'emploi — filtres `?skill=` `?dept_code=` `?limit=` |
| `GET` | `/stats` | Usage développeurs SO — filtre `?skill=` ; sans filtre : top 50 de 2025 |
| `GET` | `/trainings` | Liste toutes les formations |
| `GET` | `/trainings/skill/{name}` | Formations pour un skill donné |

Voir [docs/openapi.md](docs/openapi.md) pour la référence complète avec exemples curl.

---

## Structure du projet

```
skillwatch/
├── main.py                     # CLI extraction (--step, --source, --dry-run)
├── Justfile                    # Task runner
├── docker-compose.yml          # PostgreSQL (warehouse)
├── sql/
│   └── schema_app.sql          # app.users (auth API), hors dbt — état OLTP
├── dbt_skillwatch/             # Transform : staging → intermediate → marts
│   ├── models/
│   │   ├── staging/            # Vues, nettoyage léger depuis raw.*
│   │   ├── intermediate/       # Vues, logique métier
│   │   └── marts/              # Tables matérialisées (skills, market_summary, ...)
│   └── seeds/
│       ├── departments.csv     # Population INSEE par département
│       ├── skills_categories.csv
│       └── skills_mapping.csv  # ~450 aliases → canonicals
├── src/
│   ├── extract/
│   │   ├── france_travail.py   # API REST France Travail → raw.*
│   │   ├── stackoverflow_latest.py  # CSV Stack Overflow → raw.*
│   │   ├── stackoverflow_spark.py   # Archives SO via Spark → raw.*
│   │   ├── openclassrooms.py   # Scraping Playwright → raw.*
│   │   └── match_skills_france_travail.py  # Matching skills France Travail (network-free)
│   ├── api/
│   │   ├── main.py             # Application FastAPI
│   │   ├── routes/             # auth, skills, market, trainings, jobs, stats
│   │   ├── schemas/            # Modèles Pydantic
│   │   ├── services/           # Requêtes SQL (skillwatch_warehouse)
│   │   └── core/               # Config, sécurité JWT
│   └── utils/
│       ├── db.py               # Moteurs SQLAlchemy
│       └── logger.py
└── docs/
    ├── openapi.md              # Référence API complète
    ├── merise_mcd.md           # Modélisation Merise (MCD/MPD)
    └── ...
```

---

## Base de données

```bash
# Vérifier les tables
just db-check

# Réinitialiser complètement
just db-reset
```

| Instance | Port | Base | Contenu |
|----------|------|------|---------|
| postgres_warehouse | 5432 | skillwatch_warehouse | `raw.*` (extraction brute) · `public.*` (seeds dbt) · `marts.*` (skills, market_summary, ...) · `app.*` (auth API) |
| postgres_warehouse | 5432 | skillwatch_db | Legacy, conservée jusqu'au décommissionnement complet — plus utilisée par le code applicatif |
