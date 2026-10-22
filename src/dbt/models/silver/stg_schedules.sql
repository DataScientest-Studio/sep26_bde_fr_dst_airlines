{{ config(materialized='table',schema='silver',
        unique_key='id',post_hook=[
      "CREATE INDEX IF NOT EXISTS idx_stg_schedule_dep_airport ON {{ this }} (dep_airport_id)",
      "CREATE INDEX IF NOT EXISTS idx_stg_schedule_arr_airport ON {{ this }} (arr_airport_id)",
      "CREATE INDEX IF NOT EXISTS idx_stg_schedule_airline ON {{ this }} (airline_id)",
      "CREATE INDEX IF NOT EXISTS idx_stg_schedule_flight_icao ON {{ this }} (flight_icao)",
      "GRANT SELECT ON ALL TABLES IN SCHEMA silver TO airline_rw"
    ]) }}
-- Recupere les schedules et calcule le rn pour pouvoir supprimer les vol operes par une filiale (on garde le vol commercial)
with schedules as (
    select a.*,    
        TO_CHAR(dep_time, 'HH24:MI')  AS dep_hour,
        TO_CHAR(arr_time, 'HH24:MI')  AS arr_hour,
        EXTRACT(DOW FROM dep_time) AS dow,
        row_number() over (
            partition by
                flight_number,
                dep_icao,
                dep_icao,
                arr_time,
                dep_time,
                EXTRACT(DOW FROM dep_time) 
            order by
                case
                    when cs_flight_iata is not null then 1
                    else 2
                end
        ) as rn 
        from {{ source('raw', 'airlabs_schedules') }} a
        where status='landed'
),
-- Garde que les vols commerciaux
dedup_schedules as (
    select *
    from schedules
    where rn = 1
),
-- Recupere les aeroports pour ajoute l'airport id
airports as (SELECT * FROM {{ref('stg_airports')}}),
-- Recupere les compagnies pour ajoute l'airline id
airlines as (SELECT * FROM {{ref('stg_airlines')}}),
-- Requete finale
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
        ]) }} AS flight_id,   -- Calcul l'ID du Vol (comme fait dans stg_flights)
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
        s.dep_time,
        s.dep_actual,
        s.arr_time,
        s.arr_actual,
        s.duration,
        s.arr_delayed as delayed
FROM dedup_schedules s 
LEFT JOIN airports da ON s.dep_iata=da.iata_code
LEFT JOIN airports aa ON s.arr_iata=aa.iata_code
LEFT JOIN airlines al ON s.airline_icao= al.icao_code
WHERE s.status = 'landed'
)

select * from final