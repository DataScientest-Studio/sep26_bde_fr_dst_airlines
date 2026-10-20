--###############################################
--# raw.airlabs_airlines -> silver.stg_airlines
--###############################################

{{ config(materialized='incremental',
        unique_key='airline_id',post_hook=[
      "CREATE INDEX IF NOT EXISTS idx_stg_airlines_icao ON {{ this }} (icao_code)"
    ]) }}

with Airlines as (
    select *
        from {{ source('raw', 'airlabs_airlines') }} a
),
final as (
    SELECT DISTINCT 
        {{ dbt_utils.generate_surrogate_key([
            'icao_code'
        ]) }} AS airline_id,
		name as airline_name,
	    iata_code,
	    icao_code
    FROM Airlines  
    WHERE icao_code IS NOT NULL
)
select * from final