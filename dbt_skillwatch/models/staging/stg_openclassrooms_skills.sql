with source as (

    select * from {{ source('raw', 'openclassrooms_skills') }}

)

select
    url,
    skill_raw
from source
