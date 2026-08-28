{{ config(materialized='table') }}

with latest as (

    -- int_stackoverflow_skills (CSV latest) n'a pas de colonne survey_year : une seule
    -- année source (2025), ajoutée en dur ici plutôt que dans le modèle intermediate.
    select
        canonical_skill,
        2025 as survey_year,
        usage_count,
        avg_salary_usd
    from {{ ref('int_stackoverflow_skills') }}

),

archive as (

    select
        canonical_skill,
        survey_year,
        usage_count,
        avg_salary_usd
    from {{ ref('int_stackoverflow_archive_skills') }}

)

select * from latest
union all
select * from archive
