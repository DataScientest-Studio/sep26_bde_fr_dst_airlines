{{ config(materialized='table', schema='gold',
    post_hook=["GRANT SELECT ON {{ this }} TO airline_rw"]) }}

select
    id as schedule_id,
    flight_id,
    flight_icao,
    airline_id,
    dep_airport_id,
    arr_airport_id,
    dep_iata,
    arr_iata,
    dep_time,
    arr_time as sched_arr_utc,
    arr_actual as actual_arr_utc,
    date_trunc('hour', arr_time) as arr_hour,
    extract(isodow from arr_time at time zone 'Europe/Paris') as dow,
    extract(hour from arr_time at time zone 'Europe/Paris') as arr_hour_local,
    coalesce(delayed, 0) as arr_delay_min,
    case
        when delayed > 15 then true
        else false
    end as delay
from {{ ref('stg_schedules') }}