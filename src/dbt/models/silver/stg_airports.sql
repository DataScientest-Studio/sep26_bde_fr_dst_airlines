--###############################################
--# raw.airlabs_airports -> silver.stg_airports
--###############################################

{{ config(materialized='table',schema='silver',
        unique_key='airport_id',
        post_hook=[
      "CREATE INDEX IF NOT EXISTS idx_stg_airports_icao ON {{ this }} (icao_code)"
    ]) }}

with airports as (
    select *
        from {{ source('raw', 'airlabs_airports') }} a
),
dedup as (

    select *,
           row_number() over (
               partition by icao_code
               order by icao_code
           ) as rn
    from airports
    where icao_code is not null

),
final as (
    SELECT DISTINCT 
        {{ dbt_utils.generate_surrogate_key([
            'icao_code'
        ]) }} AS airport_id,
		name as airport_name,
	    iata_code,
	    icao_code,
	    lat,
	    lng,
	    country_code,
	    '' as city
    FROM dedup  
    WHERE rn=1
)
select * from final