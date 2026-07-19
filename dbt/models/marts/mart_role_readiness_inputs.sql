with demand as (
    select role_key, skill_key, sum(job_demand) as job_demand
    from {{ ref('mart_role_skill_demand') }}
    group by role_key, skill_key
),
supply as (
    select skill_key, sum(coverage_count) as course_supply
    from {{ ref('fact_course_skill_coverage') }}
    group by skill_key
)
select
    d.role_key,
    d.skill_key,
    d.job_demand,
    coalesce(s.course_supply, 0) as course_supply,
    d.job_demand - coalesce(s.course_supply, 0) as readiness_gap
from demand d
left join supply s using (skill_key)
