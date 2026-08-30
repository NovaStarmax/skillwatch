{{ config(materialized='table') }}

with all_skills as (

    -- UNION (pas UNION ALL) : dédoublonne les canonical_skill communs aux 3 sources
    -- (ex. "Python" apparaît dans les 3 marts) avant la jointure catégories, sans quoi
    -- un même skill produirait une ligne par source dans le résultat final.
    select canonical_skill from {{ ref('stackoverflow_skills') }}
    union
    select canonical_skill from {{ ref('training_skills') }}
    union
    select canonical_skill from {{ ref('job_offer_skills') }}

)

select
    all_skills.canonical_skill as skill_name,
    -- left join volontaire : un skill sans catégorie connue dans le seed (curation manuelle,
    -- ~308 associations) doit rester dans le résultat, catégorie 'unknown' plutôt que disparaître.
    coalesce(skills_categories.category, 'unknown') as category
from all_skills
left join {{ ref('skills_categories') }} as skills_categories
    on all_skills.canonical_skill = skills_categories.skill_name
