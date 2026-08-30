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

# dbt seed (charge departments/skills_categories/skills_mapping dans public)
dbt-seed:
  cd dbt_skillwatch && uv run dbt seed

# Transform : staging → intermediate → marts (dbt), remplace l'ancien normalizer.py
transform:
  cd dbt_skillwatch && uv run dbt build

# Lance l'API
api:
  uv run uvicorn src.api.main:app --reload --port 8000


# Vérifie la DB (skillwatch_warehouse : raw/public/marts/app)
db-check:
  docker compose exec postgres_warehouse psql -U skillwatch -d skillwatch_warehouse -c "\dt raw.*" -c "\dt public.*" -c "\dt marts.*" -c "\dt app.*"

# Crée skillwatch_warehouse (raw/staging/marts dbt) — connexion d'ancrage sur la base admin
# "postgres" (toujours présente nativement), pas sur une base "legacy" utilisée comme simple
# point de connexion technique. Postgres n'a pas de CREATE DATABASE IF NOT EXISTS, on tolère
# l'erreur si elle existe déjà.
# app.users (auth API) vit dans skillwatch_warehouse mais hors dbt (state OLTP, pas analytique) — schema_app.sql, pas un modèle/seed dbt
db-init-warehouse:
  docker compose exec -T postgres_warehouse psql \
    -U skillwatch -d postgres -c "CREATE DATABASE skillwatch_warehouse;" 2>/dev/null || true
  docker compose exec -T postgres_warehouse psql \
    -U skillwatch -d skillwatch_warehouse -c "CREATE SCHEMA IF NOT EXISTS raw;"
  docker compose exec -T postgres_warehouse psql \
    -U skillwatch -d skillwatch_warehouse < sql/schema_app.sql
  echo "Base skillwatch_warehouse prête"

# Initialise les bases de données depuis zéro (schéma + seeds dbt, plus de schema_warehouse.sql/schema_demographics.sql)
db-init: db-init-warehouse
  just dbt-seed
  echo "Bases initialisées"

# Réinitialise complètement les bases (supprime tout)
db-reset:
  docker compose down -v
  docker compose up -d postgres_warehouse
  sleep 5
  just db-init
