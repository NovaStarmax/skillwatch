# SkillWatch — Registre des Traitements (C4)

## Position générale

SkillWatch ne collecte aucune donnée personnelle nominative au sens du RGPD (Règlement UE 2016/679).

Conformément au Considérant 26 du RGPD :

> "Les données anonymisées ne sont pas soumises au présent règlement."

Toutes les sources utilisées sont soit anonymisées à la source, soit des données d'entreprises ou
des statistiques agrégées.

## Analyse par source

| Source | Données collectées | Données personnelles ? | Justification |
|--------|-------------------|----------------------|---------------|
| France Travail | Offres d'emploi (entreprises) | ❌ Non | Données entreprises, pas de candidats |
| Stack Overflow Survey | ResponseId anonyme, stats agrégées | ❌ Non | Anonymisé à la source par Stack Overflow |
| OpenClassrooms | Fiches formations publiques | ❌ Non | Données publiques, aucun apprenant |
| INSEE | Population par département | ❌ Non | Données agrégées, aucune granularité individuelle |

## Traitement borderline : table users

La table `users` stocke des identifiants administrateurs.

| Champ | Valeur | Qualification |
|-------|--------|---------------|
| username | "admin" | Identifiant technique |
| hashed_password | Hash Argon2 | Non réversible |

**Conclusion :** traitement limité à un usage technique interne, pas de traitement à grande échelle,
hors périmètre d'un registre formel RGPD.

## Conclusion

SkillWatch ne nécessite pas de registre de traitements au sens de l'article 30 du RGPD car aucune
donnée personnelle nominative n'est traitée.

Ce document constitue la justification documentée de cette position.
