# SkillWatch API — Référence

Observatoire du marché de l'emploi Data & IA en France.  
Base URL : `http://localhost:8000`  
Documentation interactive : `/docs` (Swagger UI) · `/redoc` (ReDoc)

---

## Authentification

Toutes les routes (sauf `/health`) requièrent un token JWT passé en header `Authorization`.

### Obtenir un token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "<ADMIN_PASSWORD du .env>"}'
```

**Réponse :**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Le token est valable **30 minutes**. Réutilisez-le pour tous les appels suivants :

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
curl http://localhost:8000/skills \
  -H "Authorization: Bearer $TOKEN"
```

---

## Endpoints

### Health

#### `GET /health`

Vérification de l'état du service. Ne nécessite pas d'authentification.

```bash
curl http://localhost:8000/health
```

**Réponse :**
```json
{"status": "ok", "service": "SkillWatch API"}
```

---

### Skills

#### `GET /skills`

Liste tous les skills connus avec leurs statistiques agrégées. Triés par nombre d'offres décroissant.

```bash
curl http://localhost:8000/skills \
  -H "Authorization: Bearer $TOKEN"
```

**Réponse (extrait) :**
```json
[
  {
    "name": "Python",
    "category": "language",
    "job_offer_count": 4821,
    "developer_usage_count": 18340,
    "avg_salary_eur": 48200.0,
    "training_count": 12
  },
  {
    "name": "SQL",
    "category": "database",
    "job_offer_count": 3104,
    "developer_usage_count": 11200,
    "avg_salary_eur": 43500.0,
    "training_count": 8
  }
]
```

#### `GET /skills/{name}`

Détail d'un skill par son nom canonique. La recherche est insensible à la casse.

```bash
curl "http://localhost:8000/skills/Python" \
  -H "Authorization: Bearer $TOKEN"
```

**Réponse :**
```json
{
  "name": "Python",
  "category": "language",
  "job_offer_count": 4821,
  "developer_usage_count": 18340,
  "avg_salary_eur": 48200.0,
  "training_count": 12
}
```

Retourne **404** si le skill n'existe pas.

---

### Market

#### `GET /market/summary`

Top 20 skills les plus demandés en offres d'emploi France Travail, avec salaire moyen, popularité Stack Overflow et département le plus actif.

```bash
curl http://localhost:8000/market/summary \
  -H "Authorization: Bearer $TOKEN"
```

**Réponse (extrait) :**
```json
[
  {
    "skill": "Python",
    "category": "language",
    "job_offer_count": 4821,
    "developer_usage_count": 18340,
    "avg_salary_eur": 48200.0,
    "training_count": 12,
    "top_dept": "75",
    "top_dept_name": "Paris",
    "top_dept_population": 2161000
  },
  {
    "skill": "SQL",
    "category": "database",
    "job_offer_count": 3104,
    "developer_usage_count": 11200,
    "avg_salary_eur": 43500.0,
    "training_count": 8,
    "top_dept": "69",
    "top_dept_name": "Rhône",
    "top_dept_population": 1843000
  }
]
```

#### `GET /market/by-department`

Offres par département, croisées avec les données démographiques INSEE. Retourne les 20 départements les plus actifs avec le ratio offres/million d'habitants.

```bash
curl http://localhost:8000/market/by-department \
  -H "Authorization: Bearer $TOKEN"
```

**Réponse (extrait) :**
```json
[
  {
    "dept_code": "75",
    "dept_name": "Paris",
    "job_count": 9840,
    "population": 2161000,
    "jobs_per_million_hab": 4553.0
  },
  {
    "dept_code": "31",
    "dept_name": "Haute-Garonne",
    "job_count": 1230,
    "population": 1400000,
    "jobs_per_million_hab": 878.6
  }
]
```

---

### Trainings

#### `GET /trainings`

Liste toutes les formations OpenClassrooms scrapées, filtrées sur les domaines tech. Triées par domaine puis titre.

```bash
curl http://localhost:8000/trainings \
  -H "Authorization: Bearer $TOKEN"
```

**Réponse (extrait) :**
```json
[
  {
    "title": "Devenez un expert de la data avec Python",
    "domain": "Data",
    "level": "Avancé",
    "duration_months": 12,
    "provider": "OpenClassrooms",
    "url": "https://openclassrooms.com/fr/paths/..."
  },
  {
    "title": "Développez des applications Web avec Angular",
    "domain": "Développement",
    "level": "Intermédiaire",
    "duration_months": 6,
    "provider": "OpenClassrooms",
    "url": "https://openclassrooms.com/fr/paths/..."
  }
]
```

#### `GET /trainings/skill/{skill_name}`

Formations disponibles pour apprendre un skill donné. Recherche insensible à la casse.

```bash
curl "http://localhost:8000/trainings/skill/Python" \
  -H "Authorization: Bearer $TOKEN"
```

**Réponse :**
```json
[
  {
    "title": "Devenez un expert de la data avec Python",
    "domain": "Data",
    "level": "Avancé",
    "duration_months": 12,
    "provider": "OpenClassrooms",
    "url": "https://openclassrooms.com/fr/paths/..."
  }
]
```

Retourne une liste vide `[]` si aucune formation ne couvre ce skill.

---

## Codes d'erreur

| Code | Description |
|------|-------------|
| `200` | Succès |
| `401` | Token manquant, invalide ou expiré |
| `404` | Ressource introuvable (skill inexistant) |
| `422` | Corps de requête invalide (validation Pydantic) |
| `500` | Erreur interne serveur |

### Exemple de réponse 401

```json
{"detail": "Token invalide ou expiré"}
```

### Exemple de réponse 404

```json
{"detail": "Skill 'Cobol' introuvable"}
```

---

## Sources de données

| Source | Type | Contenu |
|--------|------|---------|
| France Travail | API REST | Offres d'emploi tech en temps réel |
| Stack Overflow | Archives CSV (Spark) | Enquêtes développeurs 2021-2025 |
| OpenClassrooms | Scraping Playwright | Catalogue formations tech (~80 parcours) |
| INSEE | PostgreSQL | Population par département |

---

## Standards

L'API suit la spécification **OpenAPI 3.1**.  
Le schéma JSON complet est disponible à : `GET /openapi.json`
