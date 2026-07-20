with normalized as (
    select
        *,
        case role_category
            when 'Data Analytics' then 'Data Analyst'
            when 'Data Architecture' then 'Data Engineer'
            when 'Data Engineering' then 'Data Engineer'
            when 'Data Science' then 'Data Scientist'
            when 'Other Data Role' then 'Other Technology Role'
            else role_category
        end as normalized_role_category
    from {{ source('market_intel', 'skill_trend_history') }}
)
select
    md5(concat_ws('|', run_id, source_name, skill, location, normalized_role_category)) as skill_trend_key,
    md5(skill) as skill_key,
    md5(normalized_role_category) as role_key,
    md5(location) as location_key,
    md5(source_name) as source_key,
    md5(run_id) as time_key,
    run_id,
    run_timestamp,
    job_count,
    course_count,
    salary_min_avg,
    salary_max_avg
from normalized
