# SkillWatch — Procédures de Conformité RGPD (C4)

## Principe général

Les procédures ci-dessous s'appliquent aux comptes administrateurs
(table `users`) et aux données opérationnelles du pipeline.
Chaque procédure précise son mode d'exécution (manuelle ou automatisée)
et sa fréquence d'application.

## Tableau des procédures de conformité

| Procédure | Mode | Fréquence | Traitement de conformité |
|-----------|------|-----------|--------------------------|
| Revue des comptes admin | **Manuelle** | Mensuelle | Vérifier que chaque entrée de la table `users` correspond à un administrateur actif ; supprimer les comptes orphelins |
| Suppression compte admin | **Manuelle** | À chaque départ | Exécuter la procédure SQL de suppression (voir Procédure 1) ; délai de traitement : immédiat |
| Rotation du secret JWT | **Manuelle** | Tous les 6 mois | Régénérer `JWT_SECRET_KEY` dans `.env`, redémarrer l'API — invalide tous les tokens en cours |
| Purge des offres obsolètes | **Manuelle** | Tous les 6 mois | Supprimer les enregistrements `job_offers` de plus de 6 mois (données publiques d'entreprises, bonne pratique) |
| Purge des logs techniques | **Manuelle** | Tous les 6 mois | Supprimer `data/logs/*.log` — les logs ne contiennent pas de données personnelles mais sont purgés par hygiène |
| Réinitialisation complète | **Manuelle** | Sur demande (exercice de droit) | `docker compose down -v` + `just clean-scraping` + suppression des logs — suppression totale et irréversible |

Aucune procédure n'est automatisée : le volume de traitements personnels
(≤ 3 comptes administrateurs) ne justifie pas une automatisation.
Un responsable technique déclenche chaque procédure manuellement.

## Procédure 1 — Suppression d'un compte administrateur

```sql
-- Identifier le compte
SELECT id, username, created_at FROM users;

-- Supprimer le compte
DELETE FROM users WHERE username = 'nom_admin';

-- Vérifier la suppression
SELECT * FROM users WHERE username = 'nom_admin';
-- Résultat attendu : 0 lignes
```

Délai de traitement : immédiat.

## Procédure 2 — Purge des offres obsolètes

Les offres d'emploi sont des données publiques d'entreprises.
Par mesure de bonne pratique, les offres de plus de 6 mois
sont purgées manuellement :

```sql
-- Vérifier le volume à purger
SELECT COUNT(*)
FROM job_offers
WHERE published_at < NOW() - INTERVAL '6 months';

-- Purger
DELETE FROM job_offers
WHERE published_at < NOW() - INTERVAL '6 months';
```

## Procédure 3 — Rotation du secret JWT

```bash
# 1. Générer un nouveau secret
python3 -c "import secrets; print(secrets.token_hex(32))"

# 2. Mettre à jour .env
JWT_SECRET_KEY=nouveau_secret

# 3. Redémarrer l'API
# Ctrl+C pour arrêter just api
just api
```

Note : tous les tokens existants sont invalidés
immédiatement après rotation.

## Procédure 4 — Réinitialisation complète

Pour supprimer l'intégralité des données du projet :

```bash
# Supprime les volumes PostgreSQL
docker compose down -v

# Supprime le cache de scraping
just clean-scraping

# Supprime les logs
rm -rf data/logs/*.log
```

Toutes les données sont supprimées.
Aucune donnée personnelle n'est conservée en dehors
des volumes Docker.
