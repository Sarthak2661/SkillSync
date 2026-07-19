select
    md5(skill) as skill_key,
    run_id,
    job_demand,
    course_supply,
    demand_score,
    course_supply_score as supply_score,
    growth_score,
    salary_premium_score,
    saturation_score,
    opportunity_index,
    opportunity_label,
    market_direction,
    bls_growth_percent
from {{ source('market_intel', 'skill_gap_summary') }}
