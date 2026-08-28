{{ config(materialized='table') }}

select * from {{ ref('int_openclassrooms_skills') }}
