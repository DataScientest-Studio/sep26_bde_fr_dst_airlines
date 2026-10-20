--###############################################
--# silver.stg_flights -> gold.dim_flights
--###############################################
{{ config(materialized='view') }}

select *
from {{ ref( 'stg_flights') }}