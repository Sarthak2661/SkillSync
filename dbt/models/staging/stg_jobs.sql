select
    run_id,
    md5(concat_ws('|', run_id, source_name, external_id)) as job_key,
    source_name,
    source_confidence,
    external_id,
    title,
    company,
    coalesce(nullif(location, ''), 'Unknown') as location,
    remote_type,
    salary_min,
    salary_max,
    posted_at,
    url,
    skills,
    skill_confidence,
    skill_count,
    collected_at
from {{ source('market_intel', 'job_postings') }}
