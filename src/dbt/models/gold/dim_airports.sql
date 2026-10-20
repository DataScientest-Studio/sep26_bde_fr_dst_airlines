###############################################
# silver.stg_airports -> gold.dim_airports
###############################################
{{ config(materialized='view', schema="gold") }}

select *
from {{ ref( 'stg_airports') }}