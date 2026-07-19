with mentions as (
    select
        m.*,
        case
            when lower(j.title) ~ '(engineer|etl|pipeline|warehouse)' then 'Data Engineering'
            when lower(j.title) ~ '(scientist|machine learning|(^| )ml |(^| )ai )' then 'Data Science'
            when lower(j.title) ~ '(analyst|analytics|business intelligence|(^| )bi )' then 'Data Analytics'
            when lower(j.title) ~ '(architect|platform)' then 'Data Architecture'
            else 'Other Data Role'
        end as role_name,
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
