with ranked as (
    select
        *,
        row_number() over (partition by skill order by run_id desc) as row_number
    from {{ source('market_intel', 'skill_gap_summary') }}
)
select
    md5(skill) as skill_key,
    skill,
    category,
    taxonomy_source,
    onet_evidence_status,
    onet_soc_codes,
    onet_occupations
from ranked
where row_number = 1
