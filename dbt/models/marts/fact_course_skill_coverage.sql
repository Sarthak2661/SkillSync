select
    mention_key as course_skill_coverage_key,
    md5(skill) as skill_key,
    md5(m.source_name) as source_key,
    md5(m.run_id) as time_key,
    m.run_id,
    m.record_key as course_key,
    m.skill_confidence,
    1 as coverage_count
from {{ ref('int_skill_mentions') }} m
where m.mention_type = 'course'
