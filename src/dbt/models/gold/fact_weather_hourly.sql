{{ config(materialized='table', schema='gold',
    post_hook=["GRANT SELECT ON {{ this }} TO airline_rw"]) }}

-- Keep only the weather of the AirLabs period (first flight day onwards)
with period as (
    select cast(min(dep_time) as date) as first_day
    from {{ ref('stg_schedules') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['w.icao', 'w.time']) }} as weather_id,
    w.airport_id,
    w.icao,
    w.time,
    w.temperature_2m,
    w.dew_point_2m,
    w.relative_humidity_2m,
    w.pressure_msl,
    w.cloud_cover,
    w.cloud_cover_low,
    w.cloud_cover_mid,
    w.cloud_cover_high,
    w.wind_speed_10m,
    w.wind_direction_sin,
    w.wind_direction_cos,
    w.wind_gusts_10m,
    w.precipitation,
    w.rain,
    w.snowfall,
    w.weather_code
from {{ ref('stg_weather_hourly') }} w
cross join period p
where w.time >= p.first_day