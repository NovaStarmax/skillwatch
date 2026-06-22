# SkillWatch — Procédures de Conformité RGPD (C4)

## Principe général

En l'absence de données personnelles nominatives, les procédures RGPD se limitent à :

1. La gestion des comptes administrateurs
2. La suppression des données obsolètes
3. La réponse aux demandes éventuelles

## Procédure 1 — Suppression d'un compte administrateur

Si un administrateur quitte le projet :

```sql
-- Supprimer le compte
DELETE FROM users WHERE username = 'nom_admin';

-- Vérifier la suppression
SELECT * FROM users WHERE username = 'nom_admin';
-- Doit retourner 0 lignes
```

Délai : immédiat à la demande.

## Procédure 2 — Suppression des données obsolètes

Les données brutes (offres d'emploi, statistiques) ont une durée de vie limitée à leur pertinence
analytique.

Politique de rétention :

| Table | Durée de rétention | Procédure |
|-------|-------------------|-----------|
| job_offers | 6 mois | DELETE WHERE published_at < NOW() - INTERVAL '6 months' |
| survey_stats | Permanente | Données historiques, pas de suppression |
| trainings | Mise à jour à chaque run | ON CONFLICT (url) DO UPDATE |
| market_summary | Mise à jour à chaque run | ON CONFLICT (skill_id) DO UPDATE |

## Procédure 3 — Réponse à une demande de suppression

Dans le cas improbable d'une demande de suppression (seuls les admins sont concernés) :

1. Identifier le compte dans la table `users`
2. Exécuter la procédure 1
3. Confirmer la suppression par écrit
4. Délai de traitement : 72 heures maximum

## Procédure 4 — Réinitialisation complète

Pour supprimer l'intégralité des données du projet :

```bash
docker compose down -v  # Supprime les volumes PostgreSQL
just clean-scraping     # Supprime les HTML cachés
rm -rf data/logs/       # Supprime les logs
```

Toutes les données sont supprimées. Aucune donnée personnelle n'est conservée en dehors des volumes
Docker.
