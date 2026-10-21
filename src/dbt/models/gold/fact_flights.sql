with f as (
    select
        o.*,
        r.sched_arr_time,
        (cast(o.dof as date) + r.sched_arr_time) at time zone 'Europe/Paris' as sched_arr_ts
    from {{ ref('stg_opdi_flights') }} o
    left join {{ ref('stg_flight_schedule_ref') }} r
      on o.flt_id = r.flt_id and o.adep = r.adep and o.ades = r.ades
)

select
    *,
    extract(epoch from (last_seen at time zone 'UTC') - sched_arr_ts) / 60 as arr_delay_min,
    (last_seen at time zone 'UTC') - sched_arr_ts > interval '15 minutes' as delay
from f