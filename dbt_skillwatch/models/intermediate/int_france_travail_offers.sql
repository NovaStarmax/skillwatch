with staged as (

    select * from {{ ref('stg_france_travail') }}

),

parsed as (

    -- reproduction fidèle de parse_salary() (regex Python) : NULL si pas de match, comme
    -- le comportement actuel. dept_code = 2 premiers caractères du code commune INSEE.
    select
        staged.*,
        substring(staged.commune, 1, 2) as dept_code,
        regexp_match(
            staged.salaire_libelle, '(\d+(?:\.\d+)?)\s*Euros?\s*à\s*(\d+(?:\.\d+)?)'
        ) as salary_match
    from staged

)

select
    parsed.external_id,
    parsed.title,
    parsed.description,
    parsed.company,
    parsed.location,
    parsed.commune,
    parsed.dept_code,
    -- left join volontaire : le legacy n'enrichit que 464/514 offres (certains codes commune
    -- ne matchent aucun département du seed) — un inner join ferait disparaître ces offres à tort.
    departments.population as dept_population,
    parsed.contract_type,
    parsed.published_at,
    floor((parsed.salary_match[1])::numeric)::int as salary_min,
    floor((parsed.salary_match[2])::numeric)::int as salary_max
from parsed
left join {{ ref('departments') }} as departments
    on parsed.dept_code = departments.dep
