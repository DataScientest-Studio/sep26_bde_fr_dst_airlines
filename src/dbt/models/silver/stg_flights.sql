{{ config(materialized='table',schema='silver',
        unique_key='flight_id',post_hook=[
      "CREATE INDEX IF NOT EXISTS idx_stg_flight_dep_airport ON {{ this }} (dep_airport_id)",
      "CREATE INDEX IF NOT EXISTS idx_stg_flight_arr_airport ON {{ this }} (arr_airport_id)",
      "CREATE INDEX IF NOT EXISTS idx_stg_flight_airline ON {{ this }} (airline_id)",
      "CREATE INDEX IF NOT EXISTS idx_stg_flight_num ON {{ this }} (flight_number)",
      "GRANT SELECT ON ALL TABLES IN SCHEMA silver TO airline_rw"
    ]) }}

with schedules as (
    select a.*,    
        TO_CHAR(dep_time, 'HH24:MI')  AS dep_hour,
        TO_CHAR(arr_time, 'HH24:MI')  AS arr_hour,
        EXTRACT(DOW FROM dep_time) AS dow
        from {{ source('raw', 'airlabs_schedules') }} a
),
airports as (SELECT * FROM {{ref('stg_airports')}}),
airlines as (SELECT * FROM {{ref('stg_airlines')}}),
final as (
    SELECT DISTINCT 
        {{ dbt_utils.generate_surrogate_key([
            'flight_icao',
            'da.airport_id',
            'aa.airport_id',
            'dep_hour',
            'arr_hour',
            'al.airline_id',
            'dow'
        ]) }} AS flight_id,
		s.flight_icao,
        al.airline_id as airline_id,
        s.flight_number,
        da.airport_id as dep_airport_id,
        s.dep_iata,
        aa.airport_id as arr_airport_id,
        s.arr_iata,
        s.dep_hour AS dep_time,
        s.arr_hour AS arr_time,
        s.dow AS days_of_week,
        count(*) AS occurences
FROM schedules s 
LEFT JOIN airports da ON s.dep_iata=da.iata_code
LEFT JOIN airports aa ON s.arr_iata=aa.iata_code
LEFT JOIN airlines al ON s.airline_icao= al.icao_code
WHERE s.status = 'landed'
GROUP BY flight_icao,
        flight_number,
        da.airport_id,
        aa.airport_id ,
        dep_hour,
        arr_hour,
        al.airline_id,
        s.dep_iata,
        s.arr_iata,
        s.dow
)

select * from final