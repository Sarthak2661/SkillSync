select
    role_key,
    skill_key,
    time_key,
    sum(job_count) as job_demand,
    avg(salary_min_avg) as salary_min_avg,
    avg(salary_max_avg) as salary_max_avg
from {{ ref('fact_skill_trend_history') }}
group by role_key, skill_key, time_key
