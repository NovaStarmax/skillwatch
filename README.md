# SkillWatch — Observatoire du Marché de l'Emploi Data & IA

SkillWatch agrège des données issues de 5 sources hétérogènes pour répondre à une question :
**quelles compétences tech sont demandées, populaires et bien rémunérées en France ?**

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    EXTRACT                          │
│  France Travail API  ·  Stack Overflow CSV (Spark)  │
│  OpenClassrooms (Playwright)  ·  INSEE (SQL dump)   │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                   TRANSFORM                         │
│  Normalisation · Dédoublonnage · skills_mapping     │
│  Calcul market_summary · Enrichissement géo         │
└────────────────────────┬────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
  skillwatch_db (5432)    demographics_db (5433)
  Base analytique         Données INSEE
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
| INSEE | Dump SQL | Population par département |

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
# → Renseigner FRANCE_TRAVAIL_CLIENT_ID, FRANCE_TRAVAIL_CLIENT_SECRET,
#   JWT_SECRET_KEY et ADMIN_PASSWORD dans .env

# 3. Installer les dépendances Python
uv sync

# 4. Installer les navigateurs Playwright (scraping OpenClassrooms)
uv run playwright install chromium

# 5. Démarrer les services Docker
docker compose up -d

# 6. Initialiser les bases de données
just db-init
```

---

## Configuration

Copier `.env.example` → `.env` et renseigner :

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | URL PostgreSQL warehouse (skillwatch_db, port 5432) |
| `DEMOGRAPHICS_URL` | URL PostgreSQL demographics (demographics_db, port 5433) |
| `FRANCE_TRAVAIL_CLIENT_ID` | Client ID API France Travail |
| `FRANCE_TRAVAIL_CLIENT_SECRET` | Client Secret API France Travail |
| `JWT_SECRET_KEY` | Clé secrète pour la signature des tokens JWT |
| `ADMIN_USERNAME` | Identifiant administrateur API (défaut : `admin`) |
| `ADMIN_PASSWORD` | Mot de passe administrateur API |

---

## Pipeline ETL

```bash
# Lancer le pipeline complet (extract → transform)
just pipeline

# Extraire toutes les sources
just extract

# Extraire une source spécifique
just extract-france        # France Travail
just extract-stackoverflow # Stack Overflow (CSV)
just extract-spark         # Stack Overflow (Spark)
just extract-scraping      # OpenClassrooms
just extract-demographics  # INSEE

# Transformer les données (normalisation + market_summary)
just transform

# Simuler sans exécution
uv run main.py --dry-run
```

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
├── main.py                     # CLI pipeline (--step, --source, --dry-run)
├── Justfile                    # Task runner
├── docker-compose.yml          # PostgreSQL x2 + Spark + API
├── config/
│   └── skills_mapping.json     # ~450 aliases → canonicals
├── sql/
│   ├── schema_warehouse.sql    # Schéma skillwatch_db
│   ├── schema_demographics.sql # Schéma demographics_db
│   ├── demographics_dump.sql   # Données INSEE
│   └── seed_skill_categories.sql
├── src/
│   ├── extract/
│   │   ├── france_travail.py   # API REST France Travail
│   │   ├── stackoverflow_latest.py  # CSV Stack Overflow
│   │   ├── stackoverflow_spark.py   # Archives SO via Spark
│   │   ├── openclassrooms.py   # Scraping Playwright
│   │   └── demographics.py     # Import INSEE
│   ├── transform/
│   │   └── normalizer.py       # Normalisation + market_summary
│   ├── api/
│   │   ├── main.py             # Application FastAPI
│   │   ├── routes/             # auth, skills, market, trainings
│   │   ├── schemas/            # Modèles Pydantic
│   │   ├── services/           # Requêtes SQL
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
| postgres_warehouse | 5432 | skillwatch_db | Données analytiques (skills, offres, formations, market_summary) |
| postgres_demographics | 5433 | demographics_db | Population par département INSEE |
