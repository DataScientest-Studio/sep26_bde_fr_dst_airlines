{{ config(materialized='table',schema='silver',
        unique_key='id',post_hook=[
      "CREATE INDEX IF NOT EXISTS idx_stg_schedule_dep_airport ON {{ this }} (dep_airport_id)",
      "CREATE INDEX IF NOT EXISTS idx_stg_schedule_arr_airport ON {{ this }} (arr_airport_id)",
      "CREATE INDEX IF NOT EXISTS idx_stg_schedule_airline ON {{ this }} (airline_id)",
      "CREATE INDEX IF NOT EXISTS idx_stg_schedule_flight_icao ON {{ this }} (flight_icao)",
      "GRANT SELECT ON {{ this }} TO airline_rw"
    ]) }}

with landed as (
    select a.*,
        dep_time_utc at time zone 'UTC' as sched_dep_utc,
        dep_actual_utc at time zone 'UTC' as actual_dep_utc,
        arr_time_utc at time zone 'UTC' as sched_arr_utc,
        arr_actual_utc at time zone 'UTC' as actual_arr_utc
    from {{ source('raw', 'airlabs_schedules') }} a
    where status = 'landed'
),
schedules as (
    select l.*,
        TO_CHAR(sched_dep_utc, 'HH24:MI')  AS dep_hour,
        TO_CHAR(sched_arr_utc, 'HH24:MI')  AS arr_hour,
        EXTRACT(DOW FROM sched_dep_utc) AS dow,
        row_number() over (
            partition by
                flight_number,
                dep_icao,
                arr_icao,
                sched_arr_utc,
                sched_dep_utc,
                EXTRACT(DOW FROM sched_dep_utc)
            order by
                case
                    when cs_flight_iata is not null then 1
                    else 2
                end
        ) as rn
        from landed l
),
dedup_schedules as (
    select *
    from schedules
    where rn = 1
),
airports as (
    SELECT a.*
    FROM {{ref('stg_airports')}} a
    LEFT JOIN {{ref('airport_corrections')}} c ON a.icao_code = c.old_icao
    WHERE c.old_icao IS NULL
),
iata_map as (
    SELECT DISTINCT ON (iata_code) iata_code, icao_code
    FROM airports
    WHERE iata_code <> ''
    ORDER BY iata_code, icao_code
),
airlines as (SELECT * FROM {{ref('stg_airlines')}}),
final as (
    SELECT DISTINCT
        id,
        {{ dbt_utils.generate_surrogate_key([
            'flight_icao',
            'da.airport_id',
            'aa.airport_id',
            'dep_hour',
            'arr_hour',
            'al.airline_id',
            's.dow'
        ]) }} AS flight_id,
        s.flight_icao,
        al.airline_id as airline_id,
        s.airline_icao,
        da.airport_id as dep_airport_id,
        s.dep_iata,
        aa.airport_id as arr_airport_id,
        s.arr_iata,
        s.dep_hour AS dep_hour,
        s.arr_hour AS arr_hour,
        s.dow,
        s.sched_dep_utc AS dep_time,
        s.actual_dep_utc AS dep_actual,
        s.sched_arr_utc AS arr_time,
        s.actual_arr_utc AS arr_actual,
        s.duration,
        s.arr_delayed as delayed
FROM dedup_schedules s
LEFT JOIN iata_map md ON s.dep_iata = md.iata_code
LEFT JOIN iata_map ma ON s.arr_iata = ma.iata_code
LEFT JOIN airports da ON da.icao_code = coalesce(s.dep_icao, md.icao_code)
LEFT JOIN airports aa ON aa.icao_code = coalesce(s.arr_icao, ma.icao_code)
LEFT JOIN airlines al ON s.airline_icao= al.icao_code
WHERE s.status = 'landed'
)

select * from final