select
    md5(concat_ws('|', run_id, source_name, skill, location, role_category)) as skill_trend_key,
    md5(skill) as skill_key,
    md5(role_category) as role_key,
    md5(location) as location_key,
    md5(source_name) as source_key,
    md5(run_id) as time_key,
    run_id,
    run_timestamp,
    job_count,
    course_count,
    salary_min_avg,
    salary_max_avg
from {{ source('market_intel', 'skill_trend_history') }}
