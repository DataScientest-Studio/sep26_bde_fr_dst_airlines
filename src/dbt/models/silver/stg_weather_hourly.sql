select
    *,
    {{ dbt_utils.generate_surrogate_key(['icao']) }} as airport_id,
    sin(radians(wind_direction_10m)) as wind_direction_sin,
    cos(radians(wind_direction_10m)) as wind_direction_cos
from {{ source('raw', 'meteo_hourly') }}