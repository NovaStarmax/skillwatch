# Synthèse des données Stack Overflow — Divergences inter-années

## Ce que les divergences révèlent

### 1. Un noyau stable sur toutes les années (25 colonnes)

Ces colonnes existent de 2021 à 2025 avec le **même nom exact** :

| Catégorie | Colonnes stables |
|---|---|
| Identité | `ResponseId`, `MainBranch`, `Employment`, `DevType` |
| Profil | `Age`, `EdLevel`, `OrgSize`, `Country`, `Currency` |
| Compétences | `LanguageHaveWorkedWith`, `DatabaseHaveWorkedWith`, `PlatformHaveWorkedWith`, `WebframeHaveWorkedWith` |
| Salaire | `CompTotal`, `ConvertedCompYearly` |
| Expérience | `YearsCode` |
| Stack Overflow usage | `SOAccount`, `SOComm`, `SOPartFreq`, `SOVisitFreq` |

Ce sont les colonnes sur lesquelles on peut faire des comparaisons fiables entre années.

---

### 2. Une explosion du nombre de colonnes

```
2021 :  48 colonnes
2022 :  79 colonnes  (+31)
2023 :  84 colonnes  (+5)
2024 : 114 colonnes  (+30)
2025 : 172 colonnes  (+58)
```

Le questionnaire Stack Overflow grossit chaque année. Ce n'est pas un problème de qualité des données — c'est Stack Overflow qui ajoute des thématiques nouvelles. Une colonne absente en 2021 ne signifie pas une donnée manquante : la question n'existait tout simplement pas encore.

---

### 3. Colonnes disparues après 2021

Ces 6 colonnes existent uniquement en 2021, puis sont supprimées ou absorbées :

- `Age1stCode` — âge auquel le répondant a commencé à coder
- `OpSys` — système d'exploitation utilisé
- `UK_Country` / `US_State` — précision géographique sous-nationale
- `NEWStuck` / `NEWOtherComms` — questions expérimentales préfixées `NEW`, jamais reconduites

Ces colonnes ne sont pas exploitables pour des analyses multi-années.

---

### 4. L'IA : une thématique absente puis omniprésente

| Année | Colonnes AI | Ce que ça couvre |
|---|---|---|
| 2021–2022 | 0 | Rien |
| 2023 | 17 | Premiers outils IA (`AISelect`, `AIToolCurrently Using`) |
| 2024 | +12 | Intégration IA dans le workflow (`AISearchDevHaveWorkedWith`) |
| 2025 | +38 | Agents IA, orchestration, impact perçu (`AIAgentOrchestration`, `AIFrustration`) |

L'IA passe de thématique inexistante en 2021 à bloc structurant en 2025, avec 38 nouvelles colonnes en un an. C'est le reflet direct de l'adoption massive des outils IA dans les pratiques de développement.

---

### 5. Les valeurs multi-entrées (colonnes séparées par `;`)

Les colonnes de compétences ne contiennent pas une valeur unique par répondant, mais une chaîne concaténée :

```
Python;JavaScript;SQL;TypeScript
```

Cela vaut pour `LanguageHaveWorkedWith`, `DatabaseHaveWorkedWith`, `PlatformHaveWorkedWith`, et leurs équivalents. Le séparateur est systématiquement `;`. Ces colonnes ne peuvent pas être exploitées directement — elles nécessitent un split et une normalisation à l'étape Transform.

---

## Pourquoi ces données justifient un système big data

Ces données illustrent les trois dimensions classiques de la variété Big Data :

- **Variété structurelle** : le schéma change chaque année (48 → 172 colonnes). Un système relationnel classique avec un schéma fixe ne peut pas absorber cette évolution sans migrations lourdes.
- **Variété de contenu** : certaines colonnes sont des scalaires (`Country`), d'autres des listes encodées (`Python;JavaScript;SQL`), d'autres des Likert scale fragmentées en colonnes séparées (`AIAgentChallengesStrongly agree`, etc.). Un traitement uniforme est impossible.
- **Volume** : 365 000 répondants sur 5 ans, avec jusqu'à 172 dimensions par répondant. Multiplié par les autres sources (France Travail, scraping), le volume justifie un moteur distribué comme Spark pour les étapes de transformation.
