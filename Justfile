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
