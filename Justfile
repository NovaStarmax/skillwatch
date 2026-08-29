# SkillWatch — Task runner

default:
  just --list

# Lance tout le pipeline
pipeline:
  uv run main.py

# Extract toutes les sources
extract:
  uv run main.py --step extract --source all

# Extract une source spécifique
extract-france:
  uv run main.py --step extract --source france_travail

# Matching skills France Travail (network-free, replayable) — à lancer après extract-france,
# avant tout dbt run/build : alimente raw_france_travail_skills_matched dont dépend job_offer_skills
extract-france-skills:
  uv run python -m src.extract.match_skills_france_travail

extract-stackoverflow:
  uv run main.py --step extract --source stackoverflow

extract-spark:
  uv run main.py --step extract --source spark

extract-scraping:
  uv run main.py --step extract --source openclassrooms

extract-demographics:
  uv run main.py --step extract --source demographics

# Transform
transform:
  uv run main.py --step transform

# Lance l'API
api:
  uv run uvicorn src.api.main:app --reload --port 8000


# Vérifie la DB
db-check:
  docker compose exec postgres_warehouse psql -U skillwatch -d skillwatch_db -c "\dt"

# Crée skillwatch_warehouse (raw/staging/marts dbt) — Postgres n'a pas de CREATE DATABASE IF NOT EXISTS, on tolère l'erreur si elle existe déjà
db-init-warehouse:
  docker compose exec -T postgres_warehouse psql \
    -U skillwatch -d skillwatch_db -c "CREATE DATABASE skillwatch_warehouse;" 2>/dev/null || true
  docker compose exec -T postgres_warehouse psql \
    -U skillwatch -d skillwatch_warehouse -c "CREATE SCHEMA IF NOT EXISTS raw;"
  echo "Base skillwatch_warehouse prête"

# Initialise les bases de données depuis zéro
db-init: db-init-warehouse
  docker compose exec -T postgres_warehouse psql \
    -U skillwatch -d skillwatch_db < sql/schema_warehouse.sql
  docker compose exec -T postgres_demographics psql \
    -U skillwatch -d demographics_db < sql/schema_demographics.sql
  docker compose exec -T postgres_demographics psql \
    -U skillwatch -d demographics_db < sql/demographics_dump.sql
  echo "Bases initialisées"

# Réinitialise complètement les bases (supprime tout)
db-reset:
  docker compose down -v
  docker compose up -d postgres_warehouse postgres_demographics
  sleep 5
  just db-init
