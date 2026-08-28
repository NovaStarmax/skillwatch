with source as (

    select * from {{ source('raw', 'openclassrooms_trainings') }}

)

select
    title,
    domain,
    level,
    duration_months,
    url,
    provider
from source
