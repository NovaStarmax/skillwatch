with staged as (

    select * from {{ ref('stg_openclassrooms_skills') }}

)

-- distinct : par précaution, même risque de doublon que sur les sources Stack Overflow
-- (deux alias bruts différents pour une même formation pouvant pointer vers le même skill
-- canonique, ex. "angular" + "angularjs" dans deux lignes skill_raw distinctes).
select distinct
    staged.url,
    skills_mapping.canonical_skill
from staged
inner join {{ ref('skills_mapping') }} as skills_mapping
    on staged.skill_raw = skills_mapping.alias
