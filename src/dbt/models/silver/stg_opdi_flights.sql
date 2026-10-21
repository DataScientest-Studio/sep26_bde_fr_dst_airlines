with source as (
    select * from {{ source('raw', 'opdi_flights') }}
),
--
cleaned as (
    select
        s.id,
        trim(s.flt_id) as flt_id,
        left(trim(s.flt_id), 3) as company,
        s.icao24,
        s.registration,
        s.typecode,
        s.icao_aircraft_class,
        coalesce(c.new_icao, s.adep) as adep,
        s.ades,
        s.dof,
        s.first_seen,
        s.last_seen
    from source s
    left join {{ ref('icao_corrections') }} c on s.adep = c.old_icao
    where s.ades in ('LFPG', 'LFPO', 'LFOB')
      and s.adep ~ '^[A-Z]{4}$'
      and cast(s.dof as date) not in (select excluded_date from {{ ref('excluded_dates') }})
      and s.first_seen - s.dof > interval '5 seconds'
      and trim(s.flt_id) ~ '^[A-Z]{3}[0-9]'
)

select
    *,
    date_trunc('hour', first_seen) as dep_hour,
    date_trunc('hour', last_seen) as arr_hour,
    extract(epoch from last_seen - first_seen) / 60 as duration_min
from cleaned
where adep not in ('LFPG', 'LFPO', 'LFOB')