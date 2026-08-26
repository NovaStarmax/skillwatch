with source as (

    select * from {{ source('raw', 'stackoverflow_latest') }}

)

select
    "ResponseId" as response_id,
    "LanguageHaveWorkedWith" as language_have_worked_with,
    "DatabaseHaveWorkedWith" as database_have_worked_with,
    "PlatformHaveWorkedWith" as platform_have_worked_with,
    "WebframeHaveWorkedWith" as webframe_have_worked_with,
    cast("ConvertedCompYearly" as numeric) as salary_usd
from source
