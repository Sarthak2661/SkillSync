# Roadmap

The current release covers ingestion, quality checks, warehouse loading, orchestration, API access, dashboard views, and Power BI exports. The next work should improve evidence quality rather than add more surfaces.

## Data Coverage

- Normalize salary currency and geography before comparing wage signals.
- Add another documented job API with richer data-role descriptions.
- Add parser fixtures whenever a source connector changes.
- Tighten role classification for Analyst, BI, Engineer, Scientist, and ML/AI roles.

## Trends And Scoring

- Replace fallback growth assumptions after enough weekly history exists.
- Add confidence intervals or minimum-sample rules to trend claims.
- Evaluate skill co-occurrence clusters by role category.

## Warehouse And BI

- Add PostgreSQL integration tests to CI with a temporary service container.
- Add warehouse views for Power BI direct query.
- Consider dbt only if warehouse transformations become the primary modeling layer.

## Dashboard

- Add saved role presets for common data-career paths.
- Surface low-coverage warnings beside affected charts.
- Add a weekly summary after at least seven daily snapshots are available.