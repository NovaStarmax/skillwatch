# SkillWatch — Présentation du Projet

## Contexte métier

Antoine Gobbe, Chargé de Mission Data & IA à l'Office de
Tourisme et des Congrès de Marseille (OTCM), a développé
SkillWatch pour répondre à un besoin concret de veille sur
les compétences Data & IA du marché.

L'OTCM engage des ressources humaines et des partenariats
formations. Pour piloter ces décisions, il fallait un outil
capable de croiser les offres d'emploi réelles, les
statistiques développeurs et le catalogue de formations
disponibles.

## Acteurs

| Acteur | Rôle |
|--------|------|
| Antoine Gobbe | Développeur — conception, développement, déploiement |
| OTCM | Commanditaire — besoin de veille marché compétences tech |
| France Travail | Fournisseur données offres d'emploi (API publique) |
| Stack Overflow | Fournisseur données développeurs (Survey annuel) |
| OpenClassrooms | Fournisseur données formations (site public) |
| INSEE | Fournisseur données démographiques (open data) |

## Objectifs

Répondre à trois questions métier :
1. Quelles compétences tech sont les plus demandées en France ?
2. Quelles compétences sont les mieux rémunérées ?
3. Où se former sur ces compétences ?

## Contraintes

| Contrainte | Détail |
|-----------|--------|
| Données | Sources publiques uniquement, licences ouvertes |
| Légale | Aucune donnée personnelle nominative collectée |
| Stack | Python 3.12, uv, PostgreSQL, PySpark, FastAPI |
| Budget | 0€ — APIs gratuites, infrastructure VPS existante |
| Délai | 1 semaine de développement |

## Spécifications Techniques

### Stack technique

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Langage | Python 3.12 | Pipeline ETL + API |
| Package manager | uv | Gestion dépendances |
| Base analytique | PostgreSQL 16 | Stockage final |
| Base source | PostgreSQL 16 | Données INSEE |
| Big Data | Apache Spark 3.5 | Archives Stack Overflow |
| API | FastAPI | Exposition REST |
| Scraping | Playwright + BeautifulSoup4 | OpenClassrooms |
| Auth | JWT + Argon2 | Sécurisation API |
| Orchestration | Justfile | Lancement pipeline |
| Conteneurs | Docker Compose | Environnement reproductible |

### Sources de données

| Source | Type | Accessibilité |
|--------|------|---------------|
| France Travail API | API REST OAuth2 | Compte développeur gratuit |
| Stack Overflow Survey 2025 | Fichier CSV | Téléchargement public |
| Stack Overflow Survey 2021-2024 | Big Data Spark | Téléchargement public |
| OpenClassrooms /fr/paths | Scraping Web | Page publique |
| INSEE Démographie | PostgreSQL dump | Open data data.gouv.fr |

### Point de lancement

```bash
just pipeline   # Lance l'extraction complète + transformation
just api        # Démarre l'API REST sur localhost:8000
```

## Planning

| Phase | Contenu |
|-------|---------|
| Modélisation | Schéma PostgreSQL, MCD/MPD Merise |
| Infrastructure | Docker, deux instances PostgreSQL |
| Extraction | 5 extracteurs indépendants |
| Transformation | Normalisation, agrégation market_summary |
| API | FastAPI, JWT, 6 endpoints |
| Documentation | OpenAPI, Merise, RGPD |
