{{ config(materialized='table',schema='silver',
        unique_key='id',post_hook=[
      "CREATE INDEX IF NOT EXISTS idx_stg_schedule_dep_airport ON {{ this }} (dep_airport_id)",
      "CREATE INDEX IF NOT EXISTS idx_stg_schedule_arr_airport ON {{ this }} (arr_airport_id)",
      "CREATE INDEX IF NOT EXISTS idx_stg_schedule_airline ON {{ this }} (airline_id)",
      "CREATE INDEX IF NOT EXISTS idx_stg_schedule_flight_num ON {{ this }} (flight_number)",
      "GRANT SELECT ON ALL TABLES IN SCHEMA silver TO airline_rw"
    ]) }}

with schedules as (
    select a.*,    
        TO_CHAR(dep_time, 'HH24:MI')  AS dep_hour,
        TO_CHAR(arr_time, 'HH24:MI')  AS arr_hour,
        row_number() over (
            partition by
                flight_number,
                dep_iata,
                arr_iata,
                TO_CHAR(dep_time, 'HH24:MI'),
                TO_CHAR(arr_time, 'HH24:MI')
            order by
                case
                    when cs_flight_icao is not null then 1
                    else 2
                end
        ) as rn 
        from {{ source('raw', 'airlabs_schedules') }} a
        where status='landed'
),
dedup_schedules as (
    select *
    from schedules
    where rn = 1
),
airports as (SELECT * FROM {{ref('stg_airports')}}),
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
            'al.airline_id'
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
        s.dep_time,
        s.arr_time,
        s.duration,
        s.arr_delayed as delayed
FROM dedup_schedules s 
LEFT JOIN airports da ON s.dep_iata=da.iata_code
LEFT JOIN airports aa ON s.arr_iata=aa.iata_code
LEFT JOIN airlines al ON s.airline_icao= al.icao_code
WHERE s.status = 'landed'
)

select * from final