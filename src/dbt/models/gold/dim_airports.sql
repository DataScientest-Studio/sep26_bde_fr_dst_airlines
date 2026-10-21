--###############################################
--# silver.stg_airports -> gold.dim_airports
--###############################################
{{ config(materialized='view',schema='gold', post_hook=[
      "GRANT SELECT ON ALL TABLES IN SCHEMA gold TO airline_rw"]) }}

select *
from {{ ref( 'stg_airports') }}