{{ config(materialized='table', schema='marts',
    post_hook=["GRANT USAGE ON SCHEMA {{ this.schema }} TO airline_rw",
               "GRANT SELECT ON {{ this }} TO airline_rw"]) }}

select
    f.arr_hour_local,
    count(*) as nb_flights,
    sum(case when f.delay then 1 else 0 end) as nb_delayed,
    avg(case when f.delay then 1.0 else 0.0 end) as delay_rate,
    avg(case when f.delay then f.arr_delay_min end) as avg_delay_min
from {{ ref('fact_flights') }} f
group by f.arr_hour_local
