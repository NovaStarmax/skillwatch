with staged as (

    select * from {{ ref('stg_openclassrooms_skills') }}

)

-- distinct : par précaution, même risque de doublon que sur les sources Stack Overflow
-- (deux alias bruts différents pour une même formation pouvant pointer vers le même skill
-- canonique, ex. "angular" + "angularjs" dans deux lignes skill_raw distinctes).
-- pas de trim(lower()) ici contrairement aux modèles Stack Overflow : skill_raw est déjà
-- normalisé (strip + lower) côté scraper Python avant écriture en raw, alias du seed est
-- lui-même en lowercase — la jointure directe est donc correcte, pas un oubli.
select distinct
    staged.url,
    skills_mapping.canonical_skill
from staged
inner join {{ ref('skills_mapping') }} as skills_mapping
    on staged.skill_raw = skills_mapping.alias
