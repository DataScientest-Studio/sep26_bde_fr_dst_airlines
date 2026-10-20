###############################################
# silver.stg_airlines -> gold.dim_airlines
###############################################
{{ config(materialized='view', schema="gold") }}

select *
from {{ ref( 'stg_airlines') }}