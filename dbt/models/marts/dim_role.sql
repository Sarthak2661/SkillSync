with roles as (
    select role_category as role_name
    from {{ source('market_intel', 'skill_trend_history') }}
    union
    select case
        when lower(title) ~ '(engineer|etl|pipeline|warehouse)' then 'Data Engineering'
        when lower(title) ~ '(scientist|machine learning|(^| )ml |(^| )ai )' then 'Data Science'
        when lower(title) ~ '(analyst|analytics|business intelligence|(^| )bi )' then 'Data Analytics'
        when lower(title) ~ '(architect|platform)' then 'Data Architecture'
        else 'Other Data Role'
    end as role_name
    from {{ ref('stg_jobs') }}
)
select distinct md5(role_name) as role_key, role_name
from roles
where role_name is not null
