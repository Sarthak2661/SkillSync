with roles as (
    select
        case role_category
            when 'Data Analytics' then 'Data Analyst'
            when 'Data Architecture' then 'Data Engineer'
            when 'Data Engineering' then 'Data Engineer'
            when 'Data Science' then 'Data Scientist'
            when 'Other Data Role' then 'Other Technology Role'
            else role_category
        end as role_name,
        case
            when nullif(role_family, '') is not null then role_family
            when role_category in ('Data Analytics', 'Data Architecture', 'Data Engineering') then 'Data & Analytics'
            when role_category = 'Data Science' then 'AI & Machine Learning'
            else 'Other Technology'
        end as role_family
    from {{ source('market_intel', 'skill_trend_history') }}
    union
    select
        role_category as role_name,
        role_family
    from {{ ref('stg_jobs') }}
)
select distinct
    md5(role_name) as role_key,
    role_name,
    role_family
from roles
where role_name is not null and role_family is not null
