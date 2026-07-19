with job_mentions as (
    select
        md5(concat_ws('|', job_key, trim(skill))) as mention_key,
        'job'::text as mention_type,
        run_id,
        job_key as record_key,
        source_name,
        source_confidence,
        trim(skill) as skill,
        skill_confidence
    from {{ ref('stg_jobs') }}
    cross join lateral regexp_split_to_table(coalesce(skills, ''), '\|') as skill
    where trim(skill) <> ''
),
course_mentions as (
    select
        md5(concat_ws('|', course_key, trim(skill))) as mention_key,
        'course'::text as mention_type,
        run_id,
        course_key as record_key,
        source_name,
        source_confidence,
        trim(skill) as skill,
        skill_confidence
    from {{ ref('stg_courses') }}
    cross join lateral regexp_split_to_table(coalesce(skills, ''), '\|') as skill
    where trim(skill) <> ''
)
select * from job_mentions
union all
select * from course_mentions
