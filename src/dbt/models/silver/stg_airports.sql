--###############################################
--# raw.airlabs_airports -> silver.stg_airports
--###############################################

{{ config(materialized='incremental',
        unique_key='airport_id',
        post_hook=[
      "CREATE INDEX IF NOT EXISTS idx_stg_airports_icao ON {{ this }} (icao_code)"
    ]) }}

with Airports as (
    select *
        from {{ source('raw', 'airlabs_airports') }} a
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
    FROM Airports  
    WHERE icao_code IS NOT NULL
)
select * from final