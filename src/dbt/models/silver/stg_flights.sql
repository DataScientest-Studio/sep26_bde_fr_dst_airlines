{{ config(schema='silver',materialized='incremental',
        unique_key='flight_id',) }}

with Schedule as (
    select a.*,    
        EXTRACT(HOUR FROM a.dep_time) AS dep_hour,
        EXTRACT(HOUR FROM a.arr_time) AS arr_hour 
        from {{ source('raw', 'airlabs_schedules') }} a
),
final as (


    SELECT DISTINCT 
        {{ dbt_utils.generate_surrogate_key([
            'flight_icao',
            'dep_iata',
            'arr_iata',
            'dep_hour',
            'arr_hour'
        ]) }} AS flight_id
		flight_icao,
        airline_icao,
        flight_number,
        dep_iata,
        arr_iata,
        dep_hour AS dep_time,
        arr_hour AS arr_time
FROM raw.airlabs_schedules  
WHERE status = 'landed'
GROUP BY flight_icao,
        airline_icao,
        flight_number,
        dep_iata,
        arr_iata,
        dep_hour,
        arr_hour
)

select * from final