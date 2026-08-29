with source as (

    select * from {{ source('raw', 'france_travail_skills_matched') }}

)

select
    external_id,
    canonical_skill
from source
