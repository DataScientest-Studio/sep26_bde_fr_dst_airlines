{{ config(materialized='table',schema='silver',
        unique_key='id',post_hook=[
      "CREATE INDEX IF NOT EXISTS idx_stg_schedule_dep_airport ON {{ this }} (dep_airport_id)",
      "CREATE INDEX IF NOT EXISTS idx_stg_schedule_arr_airport ON {{ this }} (arr_airport_id)",
      "CREATE INDEX IF NOT EXISTS idx_stg_schedule_airline ON {{ this }} (airline_id)",
      "CREATE INDEX IF NOT EXISTS idx_stg_schedule_flight_icao ON {{ this }} (flight_icao)",
      "GRANT SELECT ON ALL TABLES IN SCHEMA silver TO airline_rw"
    ]) }}
-- Harmonise les heures d'arrivee en UTC (anciens fichiers airlabs_raw/ en UTC, nouveaux en heure locale etiquetee +00)
with harmonized as (
    select a.*,
        case when source_file like 'airlabs_raw/%' then arr_time
             else (arr_time at time zone 'UTC') at time zone 'Europe/Paris' end as arr_time_utc,
        case when source_file like 'airlabs_raw/%' then arr_actual
             else (arr_actual at time zone 'UTC') at time zone 'Europe/Paris' end as arr_actual_utc
    from {{ source('raw', 'airlabs_schedules') }} a
    where status = 'landed'
),
-- Recupere les schedules et calcule le rn pour pouvoir supprimer les vol operes par une filiale (on garde le vol commercial)
schedules as (
    select h.*,
        TO_CHAR(dep_time, 'HH24:MI')  AS dep_hour,
        TO_CHAR(arr_time_utc, 'HH24:MI')  AS arr_hour,
        EXTRACT(DOW FROM dep_time) AS dow,
        row_number() over (
            partition by
                flight_number,
                dep_icao,
                arr_icao,
                arr_time_utc,
                dep_time,
                EXTRACT(DOW FROM dep_time)
            order by
                case
                    when cs_flight_iata is not null then 1
                    else 2
                end
        ) as rn
        from harmonized h
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
        s.arr_time_utc AS arr_time,
        s.arr_actual_utc AS arr_actual,
        s.duration,
        s.arr_delayed as delayed
FROM dedup_schedules s
LEFT JOIN airports da ON s.dep_iata=da.iata_code
LEFT JOIN airports aa ON s.arr_iata=aa.iata_code
LEFT JOIN airlines al ON s.airline_icao= al.icao_code
WHERE s.status = 'landed'
)

select * from final