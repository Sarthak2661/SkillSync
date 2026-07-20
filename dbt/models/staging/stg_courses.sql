select
    run_id,
    md5(concat_ws('|', run_id, source_name, external_id)) as course_key,
    source_name,
    source_confidence,
    external_id,
    title,
    platform,
    level,
    rating,
    duration_minutes,
    url,
    skills,
    skill_confidence,
    skill_count,
    role_families,
    collected_at
from {{ source('market_intel', 'course_listings') }}
