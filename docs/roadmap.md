# Roadmap

This is not a big product roadmap. It is just the next set of improvements that would make the project stronger as a portfolio repo and easier to trust as a small analytics system.

## Short Term

- Tighten Y Combinator filtering so broad software roles do not dilute the data-role signal.
- Add one parser test whenever a scraper or source connector changes.
- Add a simple role classifier for Analyst, BI, Engineer, Scientist, and ML/AI roles.
- Keep the README screenshots updated after dashboard layout changes.

## Data And Scoring

- Replace hand-maintained growth scores with real trend calculations after enough scheduled runs exist.
- Add source-level confidence labels so charts can separate curated, fallback, and live data.
- Add better salary normalization by currency and location.

## Warehouse And BI

- Add star-schema views for Power BI direct query.
- Add a Docker-based warehouse smoke test that runs in CI.
- Add a small dbt layer if the warehouse becomes the main analytics surface.

## Dashboard

- Add saved filter presets for analyst, data engineer, BI analyst, and data scientist views.
- Add a clearer warning when a selected source has low skill coverage.
- Add a weekly trend summary once there are at least seven days of scheduled runs.
