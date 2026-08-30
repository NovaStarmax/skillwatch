{{ config(materialized='table') }}

with job_offer_counts as (

    select
        canonical_skill,
        count(*) as job_offer_count
    from {{ ref('job_offer_skills') }}
    group by canonical_skill

),

survey_2025 as (

    -- fidèle au legacy (normalizer.py ne filtre que year = 2025) : l'archive 2021-2024
    -- est volontairement exclue de ce mart, ce n'est pas un oubli. Le legacy n'a jamais
    -- agrégé usage_count/avg_salary_usd sur plusieurs années dans market_summary.
    select
        canonical_skill,
        usage_count as developer_usage_count,
        avg_salary_usd
    from {{ ref('stackoverflow_skills') }}
    where survey_year = 2025

),

training_counts as (

    select
        canonical_skill,
        count(*) as training_count
    from {{ ref('training_skills') }}
    group by canonical_skill

),

dept_offers as (

    -- '' exclu en plus de NULL : substring() sur une commune vide renvoie '' côté SQL
    -- (stg/int france_travail), alors que le legacy Python renvoie None dans ce même cas
    -- (`dept_code = commune[:2] if commune else None`) — sans ce filtre supplémentaire,
    -- ces offres seraient comptées ici comme un "département" à part entière, ce qu'elles
    -- ne sont jamais côté legacy (46 offres concernées sur les données actuelles).
    select
        job_offer_skills.canonical_skill,
        job_offers.dept_code,
        count(*) as nb_offres
    from {{ ref('job_offer_skills') }} as job_offer_skills
    inner join {{ ref('job_offers') }} as job_offers
        on job_offer_skills.external_id = job_offers.external_id
    where job_offers.dept_code is not null
      and job_offers.dept_code != ''
    group by job_offer_skills.canonical_skill, job_offers.dept_code

),

dept_ranked as (

    select
        canonical_skill,
        dept_code,
        nb_offres,
        -- tie-break explicite (dept_code asc) : le legacy fait `ORDER BY nb_offres DESC
        -- LIMIT 1` sans second critère, donc indéterministe côté Postgres en cas d'égalité
        -- (l'ordre de retour n'est garanti par aucune clause). Ce mart, lui, est déterministe
        -- par construction. Si un cas d'égalité existe réellement dans les données, le
        -- top_dept retenu ici peut légitimement différer de celui observé sur une exécution
        -- donnée du legacy — ce n'est pas un bug de ce modèle, voir validation croisée.
        row_number() over (
            partition by canonical_skill
            order by nb_offres desc, dept_code asc
        ) as rn
    from dept_offers

),

top_dept as (

    select
        dept_ranked.canonical_skill,
        dept_ranked.dept_code,
        departments.nom as dept_name,
        departments.population as dept_population
    from dept_ranked
    left join {{ ref('departments') }} as departments
        on dept_ranked.dept_code = departments.dep
    where dept_ranked.rn = 1

)

select
    skills.skill_name,
    coalesce(job_offer_counts.job_offer_count, 0) as job_offer_count,
    coalesce(survey_2025.developer_usage_count, 0) as developer_usage_count,
    -- 0.86 : taux USD->EUR codé en dur, hérité tel quel du legacy (normalizer.py). Dette
    -- technique préexistante, pas un choix fait ici : aucune date de référence ni source
    -- documentée à l'origine, non actualisé depuis son introduction.
    round(survey_2025.avg_salary_usd * 0.86, 2) as avg_salary_eur,
    coalesce(training_counts.training_count, 0) as training_count,
    -- fidèle au legacy : top_dept ne reste renseigné que si la jointure démographique
    -- réussit aussi (le Python ne fixe top_dept que dans la branche où `d` — le résultat
    -- de la jointure departments — est trouvé), pas seulement si un département majoritaire
    -- existe. Un dept_code sans correspondance dans le seed departments donne donc NULL
    -- partout, pas juste sur le nom/population.
    case when top_dept.dept_name is not null then top_dept.dept_code end as top_dept,
    top_dept.dept_name as top_dept_name,
    top_dept.dept_population as top_dept_population,
    current_timestamp as computed_at
from {{ ref('skills') }} as skills
left join job_offer_counts
    on skills.skill_name = job_offer_counts.canonical_skill
left join survey_2025
    on skills.skill_name = survey_2025.canonical_skill
left join training_counts
    on skills.skill_name = training_counts.canonical_skill
left join top_dept
    on skills.skill_name = top_dept.canonical_skill
