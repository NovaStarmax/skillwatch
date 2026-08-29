with source as (

    select * from {{ source('raw', 'france_travail') }}

)

select
    external_id,
    title,
    description,
    company,
    location,
    commune,
    contract_type,
    published_at,
    salaire_libelle
from source
