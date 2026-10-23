{{ config(materialized='table', schema='silver',
    post_hook=["GRANT SELECT ON {{ this }} TO airline_rw"]) }}

-- Airports to collect weather for: departure and arrival airports of AirLabs flights
with used as (
    select dep_airport_id as airport_id from {{ ref('stg_schedules') }}
    union
    select arr_airport_id from {{ ref('stg_schedules') }}
)

select
    a.icao_code as icao,
    cast(a.lat as float) as latitude_deg,
    cast(a.lng as float) as longitude_deg
from {{ ref('stg_airports') }} a
join used u on u.airport_id = a.airport_id
where a.icao_code <> ''