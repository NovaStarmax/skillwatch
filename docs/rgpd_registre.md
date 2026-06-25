# SkillWatch — Registre des Traitements RGPD (Article 30)

## 1. Analyse préalable par source de données

SkillWatch ne collecte aucune donnée personnelle métier
relative à des candidats, apprenants ou répondants.

Conformément au Considérant 26 du RGPD :
> "Les données anonymisées ne sont pas soumises
> au présent règlement."

| Source | Données collectées | Données personnelles ? | Justification |
|--------|-------------------|----------------------|---------------|
| France Travail | Offres d'emploi entreprises | Non | Données entreprises, aucun candidat nominatif |
| Stack Overflow Survey | ResponseId anonyme, statistiques agrégées | Non | Anonymisé à la source par Stack Overflow |
| OpenClassrooms | Fiches formations publiques | Non | Données publiques, aucun apprenant |
| INSEE | Population par département | Non | Données agrégées, aucune granularité individuelle |
| Table `users` | username, hashed_password, created_at | Oui | Compte administrateur nominatif (voir registre ci-dessous) |

## 2. Registre formel des traitements (Article 30 RGPD)

### Traitement USERS-001 — Authentification des administrateurs API

| Champ (Art. 30 RGPD) | Valeur |
|---------------------|--------|
| **Identifiant** | USERS-001 |
| **Nom du traitement** | Authentification des administrateurs de l'API REST SkillWatch |
| **Responsable du traitement** | Antoine Gobbe — Office de Tourisme et des Congrès de Marseille (OTCM) |
| **Délégué à la Protection des Données** | Non désigné (effectif < 250 personnes, traitement non systématique) |
| **Finalité** | Sécuriser l'accès aux endpoints de l'API REST — contrôle d'accès technique |
| **Base légale** | Article 6.1.f RGPD — Intérêt légitime du responsable de traitement (sécurisation du système d'information) |
| **Catégories de personnes concernées** | Administrateurs techniques de l'OTCM (effectif ≤ 3 personnes) |
| **Catégories de données traitées** | Identifiant de connexion (username), empreinte de mot de passe (hash Argon2-id), date de création du compte |
| **Données sensibles (Art. 9)** | Aucune |
| **Destinataires** | Responsable technique SkillWatch uniquement ; accès direct en base interdit en production |
| **Transferts hors UE** | Aucun — infrastructure hébergée sur VPS OTCM en France |
| **Durée de conservation** | Durée d'exercice du rôle administrateur ; suppression immédiate au départ (Procédure 1) |
| **Mesures de sécurité techniques** | Hash Argon2-id (non réversible, résistant aux attaques par force brute), tokens JWT HS256 à durée de vie 30 minutes, rotation du secret JWT tous les 6 mois |
| **Mesures de sécurité organisationnelles** | Accès restreint aux personnes habilitées, revue mensuelle des comptes actifs |

## 3. Conclusion

Le registre ci-dessus intègre l'ensemble des traitements de données personnelles
impliqués dans la base de données SkillWatch.

Un seul traitement est identifié (USERS-001 — table `users`).
Il est documenté conformément à l'article 30 du RGPD.
Les procédures de conformité associées sont détaillées dans `rgpd_procedures.md`.
