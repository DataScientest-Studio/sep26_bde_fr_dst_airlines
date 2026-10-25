{{ config(materialized='table', schema='gold',
    post_hook=["GRANT SELECT ON {{ this }} TO airline_rw"]) }}

select
    f.schedule_id,
    f.sched_arr_utc,
    al.icao_code as airline_icao,
    da.icao_code as adep,
    aa.icao_code as ades,
    f.dow,
    f.arr_hour_local,
    w.temperature_2m as arr_temperature_2m,
    w.temperature_2m - w.dew_point_2m as arr_temp_dew_spread,
    w.relative_humidity_2m as arr_relative_humidity_2m,
    w.pressure_msl as arr_pressure_msl,
    w.cloud_cover as arr_cloud_cover,
    w.cloud_cover_low as arr_cloud_cover_low,
    w.cloud_cover_mid as arr_cloud_cover_mid,
    w.cloud_cover_high as arr_cloud_cover_high,
    w.wind_speed_10m as arr_wind_speed_10m,
    w.wind_direction_sin as arr_wind_direction_sin,
    w.wind_direction_cos as arr_wind_direction_cos,
    w.wind_gusts_10m as arr_wind_gusts_10m,
    w.precipitation as arr_precipitation,
    w.snowfall as arr_snowfall,
    w.weather_code as arr_weather_code,
    f.delay
from {{ ref('fact_flights') }} f
left join {{ ref('dim_airlines') }} al on al.airline_id = f.airline_id
left join {{ ref('dim_airports') }} da on da.airport_id = f.dep_airport_id
left join {{ ref('dim_airports') }} aa on aa.airport_id = f.arr_airport_id
left join {{ ref('fact_weather_hourly') }} w
       on w.airport_id = f.arr_airport_id
      and w.time = f.arr_hour