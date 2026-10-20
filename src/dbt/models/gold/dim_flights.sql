###############################################
# silver.stg_flights -> gold.dim_flights
###############################################
{{ config(materialized='view', schema="gold") }}

select *
from {{ ref( 'stg_flights') }}