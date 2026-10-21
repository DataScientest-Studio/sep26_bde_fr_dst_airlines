--###############################################
--# raw.airlabs_airlines -> silver.stg_airlines
--###############################################

{{ config(materialized='table',schema='silver',
        unique_key='airline_id',post_hook=[
      "CREATE INDEX IF NOT EXISTS idx_stg_airlines_icao ON {{ this }} (icao_code)"
    ]) }}

with airlines as (
    select *
        from {{ source('raw', 'airlabs_airlines') }} a
),
dedup as (

    select *,
           row_number() over (
               partition by icao_code
               order by icao_code
           ) as rn
    from airlines
    where icao_code is not null
),
final as (
    SELECT DISTINCT 
        {{ dbt_utils.generate_surrogate_key([
            'icao_code'
        ]) }} AS airline_id,
		name as airline_name,
	    iata_code,
	    icao_code
    FROM dedup  
    WHERE rn=1
)
select * from final