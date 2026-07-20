with mentions as (
    select
        m.*,
        j.role_category as role_name,
        j.location
    from {{ ref('int_skill_mentions') }} m
    join {{ ref('stg_jobs') }} j on m.record_key = j.job_key
    where m.mention_type = 'job'
)
select
    mention_key as job_skill_mention_key,
    md5(skill) as skill_key,
    md5(role_name) as role_key,
    md5(location) as location_key,
    md5(source_name) as source_key,
    md5(run_id) as time_key,
    run_id,
    record_key as job_key,
    skill_confidence,
    case when source_confidence = 'live_verified' then 1 else 0 end as high_confidence_demand,
    1 as mention_count
from mentions
