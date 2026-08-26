with staged as (

    select * from {{ ref('stg_stackoverflow_latest') }}

),

unpivoted as (

    select response_id, salary_usd, trim(lower(skill_raw)) as skill_raw
    from staged, unnest(string_to_array(language_have_worked_with, ';')) as skill_raw

    union all

    select response_id, salary_usd, trim(lower(skill_raw)) as skill_raw
    from staged, unnest(string_to_array(database_have_worked_with, ';')) as skill_raw

    union all

    select response_id, salary_usd, trim(lower(skill_raw)) as skill_raw
    from staged, unnest(string_to_array(platform_have_worked_with, ';')) as skill_raw

    union all

    select response_id, salary_usd, trim(lower(skill_raw)) as skill_raw
    from staged, unnest(string_to_array(webframe_have_worked_with, ';')) as skill_raw

),

matched as (

    -- distinct : un même répondant peut cocher plusieurs alias qui pointent vers le même
    -- skill canonique (ex. "Angular" + "AngularJS", ou "Supabase" coché à la fois en
    -- base de données et en plateforme) — sans ce distinct, son salaire serait compté
    -- plusieurs fois dans l'avg ci-dessous alors que usage_count le dédoublonne déjà.
    select distinct
        unpivoted.response_id,
        unpivoted.salary_usd,
        skills_mapping.canonical_skill
    from unpivoted
    inner join {{ ref('skills_mapping') }} as skills_mapping
        on unpivoted.skill_raw = skills_mapping.alias
    where unpivoted.skill_raw != ''

)

select
    canonical_skill,
    count(distinct response_id) as usage_count,
    avg(salary_usd) as avg_salary_usd
from matched
group by canonical_skill
