###############################################
# raw.airlabs_airlines -> silver.stg_airlines
###############################################

{{ config(schema='silver',materialized='incremental',
        unique_key='airline_id',) }}

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
	    icao_code,
    FROM Airports  
    WHERE icao_code IS NOT NULL
)
select * from final