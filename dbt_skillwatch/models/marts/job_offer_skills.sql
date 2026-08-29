{{ config(materialized='table') }}

select * from {{ ref('stg_france_travail_skills') }}
