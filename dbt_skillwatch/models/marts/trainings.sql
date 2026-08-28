{{ config(materialized='table') }}

select * from {{ ref('stg_openclassrooms_trainings') }}
