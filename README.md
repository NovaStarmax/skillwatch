# SkillWatch — Observatoire du Marché de l'Emploi Data & IA

## Description

SkillWatch est une plateforme d'observation et d'analyse du marché de l'emploi dans les domaines Data et IA. Elle agrège des données issues de plusieurs sources (France Travail, Stack Overflow, web scraping) et les expose via une API REST.

## Architecture

<!-- TODO: insérer schéma d'architecture (ETL + API + BDD) -->

## Sources de données

<!-- TODO: documenter les sources, fréquences de collecte et champs extraits -->

- France Travail API
- Stack Overflow (données publiques)
- OpenClassrooms (scraping)

## Installation

```bash
# Copier et configurer les variables d'environnement
cp .env.example .env

# Installer les dépendances
uv sync

# Démarrer les services (PostgreSQL, Spark)
docker compose up -d
```

## Usage

```bash
# Lancer tout le pipeline
uv run main.py

# Lancer une étape spécifique sur une source
uv run main.py --step extract --source france_travail

# Simulation sans exécution
uv run main.py --dry-run
```

## API

<!-- TODO: documenter les endpoints REST (OpenAPI disponible sur /docs) -->
