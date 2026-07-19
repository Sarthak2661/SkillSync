select distinct
    md5(location) as location_key,
    location
from {{ source('market_intel', 'skill_trend_history') }}
where location is not null
