select distinct
    md5(run_id) as time_key,
    run_id,
    run_timestamp,
    extract(year from run_timestamp)::int as year,
    extract(month from run_timestamp)::int as month,
    extract(week from run_timestamp)::int as week,
    extract(day from run_timestamp)::int as day
from {{ source('market_intel', 'skill_trend_history') }}
where run_timestamp is not null
