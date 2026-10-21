--###############################################
--# silver.stg_flights -> gold.dim_flights
--###############################################
{{ config(materialized='view',schema='gold', post_hook=[
      "GRANT SELECT ON ALL TABLES IN SCHEMA gold TO airline_rw"
    ]) }}

select *
from {{ ref( 'stg_flights') }}