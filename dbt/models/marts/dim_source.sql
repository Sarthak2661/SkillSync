select
    md5(source_name) as source_key,
    source_name,
    max(source_confidence) as source_confidence
from (
    select source_name, source_confidence from {{ ref('stg_jobs') }}
    union all
    select source_name, source_confidence from {{ ref('stg_courses') }}
    union all
    select source_name, 'test_source'::text as source_confidence
    from {{ source('market_intel', 'skill_trend_history') }}
) sources
group by source_name
