with schedules as (
    -- one row per flight and day across all collection files (latest file kept)
    select distinct on (flight_icao, dep_iata, arr_iata, cast(arr_time as date))
        flight_icao, dep_iata, arr_iata, dep_time, arr_time
    from {{ source('raw', 'airlabs_schedules') }}
    where flight_icao is not null
      and arr_iata in ('CDG', 'ORY', 'BVA')
    order by flight_icao, dep_iata, arr_iata, cast(arr_time as date), source_file desc
),

airports as (
    -- one ICAO per IATA to avoid N:N joins
    select distinct on (iata_code) iata_code, icao_code
    from {{ ref('stg_airports') }}
    where iata_code <> ''
    order by iata_code, icao_code
)

select
    s.flight_icao as flt_id,
    da.icao_code as adep,
    aa.icao_code as ades,
    {{ dbt_utils.generate_surrogate_key(['da.icao_code']) }} as dep_airport_id,
    {{ dbt_utils.generate_surrogate_key(['aa.icao_code']) }} as arr_airport_id,
    mode() within group (order by cast(s.dep_time as time)) as sched_dep_time,
    mode() within group (order by cast(s.arr_time as time)) as sched_arr_time,
    count(*) as nb_obs
from schedules s
join airports da on s.dep_iata = da.iata_code
join airports aa on s.arr_iata = aa.iata_code
group by 1, 2, 3, 4, 5