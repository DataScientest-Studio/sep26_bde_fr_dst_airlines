{{ config(materialized='table', schema='marts',
    post_hook=["GRANT USAGE ON SCHEMA {{ this.schema }} TO airline_rw",
               "GRANT SELECT ON {{ this }} TO airline_rw"]) }}

select
    da.icao_code as adep,
    count(*) as nb_flights,
    sum(case when f.delay then 1 else 0 end) as nb_delayed,
    avg(case when f.delay then 1.0 else 0.0 end) as delay_rate,
    avg(case when f.delay then f.arr_delay_min end) as avg_delay_min
from {{ ref('fact_flights') }} f
left join {{ ref('dim_airports') }} da on da.airport_id = f.dep_airport_id
group by da.icao_code
