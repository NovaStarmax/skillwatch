{{ config(materialized='table') }}

select * from {{ ref('int_france_travail_offers') }}
