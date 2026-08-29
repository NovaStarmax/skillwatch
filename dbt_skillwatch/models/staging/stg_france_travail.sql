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
    -- format API confirmé ISO 8601 UTC ('2026-08-27T15:59:34.470Z') sur les 514 lignes
    -- actuelles, sans exception : cast direct, pas besoin de to_timestamp() avec masque.
    published_at::timestamptz as published_at,
    salaire_libelle
from source
