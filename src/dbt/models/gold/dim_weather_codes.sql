{{ config(materialized='table', schema='gold',
    post_hook=["GRANT SELECT ON {{ this }} TO airline_rw"]) }}

select
    cast(code as int) as weather_code,
    wmo4677 as weather_code_label,
    cast(code as int) / 10 as weather_code_category,
    cast(code as int) % 10 as weather_code_subcategory
from {{ ref('weather_codes') }}