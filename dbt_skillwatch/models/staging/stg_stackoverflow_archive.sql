with source as (

    select * from {{ source('raw', 'stackoverflow_archive') }}

)

select
    response_id,
    survey_year,
    "LanguageHaveWorkedWith" as language_have_worked_with,
    "DatabaseHaveWorkedWith" as database_have_worked_with,
    "PlatformHaveWorkedWith" as platform_have_worked_with,
    "WebframeHaveWorkedWith" as webframe_have_worked_with,
    "MiscTechHaveWorkedWith" as misc_tech_have_worked_with,
    "ToolsTechHaveWorkedWith" as tools_tech_have_worked_with,
    -- "ConvertedCompYearly" contient "NA" (non-réponse, ~50% des lignes) et, pour 484 lignes
    -- de 2023 uniquement, des valeurs issues d'autres colonnes de l'enquête (ex. "Easy",
    -- "Financial Services") — décalage de colonnes localisé à ces lignes, LanguageHaveWorkedWith
    -- reste correct sur les mêmes lignes. On neutralise tout ce qui n'est pas un nombre plutôt
    -- que de lister chaque valeur corrompue individuellement.
    cast(
        case
            when "ConvertedCompYearly" ~ '^[0-9]+\.?[0-9]*$' then "ConvertedCompYearly"
            else null
        end as numeric
    ) as salary_usd
from source
