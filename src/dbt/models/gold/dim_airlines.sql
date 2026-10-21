--###############################################
--# silver.stg_airlines -> gold.dim_airlines
--###############################################
{{ config(materialized='view',schema='gold', post_hook=[
      "GRANT SELECT ON ALL TABLES IN SCHEMA gold TO airline_rw"]) }}

select *
from {{ ref( 'stg_airlines') }}