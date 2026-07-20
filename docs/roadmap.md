# Roadmap

The current release covers ingestion, quality checks, warehouse loading, orchestration, API access, dashboard views, and Power BI exports. The next work should improve evidence quality rather than add more surfaces.

## Data Coverage

- Normalize salary currency and geography before comparing wage signals.
- Add geography and seniority normalization for the existing documented job APIs.
- Add parser fixtures whenever a source connector changes.
- Measure classifier precision by role family against a labeled fixture set.

## Trends And Scoring

- Replace fallback growth assumptions after enough weekly history exists.
- Add confidence intervals or minimum-sample rules to trend claims.
- Evaluate skill co-occurrence clusters by role category.

## Warehouse And BI

- Add PostgreSQL integration tests to CI with a temporary service container.
- Add warehouse views for Power BI direct query.
- Add dbt freshness tests and source-level observability to the public CI evidence.

## Dashboard

- Add saved role presets before introducing personalized career plans or user sessions.
- Surface low-coverage warnings beside affected charts.
- Expand the weekly briefing once enough daily snapshots exist for stable week-over-week comparisons.
