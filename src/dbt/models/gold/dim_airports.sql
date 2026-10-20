--###############################################
--# silver.stg_airports -> gold.dim_airports
--###############################################
{{ config(materialized='view') }}

select *
from {{ ref( 'stg_airports') }}