{{ config(materialized='table', schema='gold',
    post_hook=["GRANT SELECT ON {{ this }} TO airline_rw"]) }}

-- One row per AirLabs flight, target = arrival delay > 15 min (delay computed by AirLabs)
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
    delayed as arr_delay_min,
        case
        when delayed is null then null
        when delayed > 15 then true
        else false
    end as delay
from {{ ref('stg_schedules') }}