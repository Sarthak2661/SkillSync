# SkillSync v2.0

SkillSync v2.0 turns the original data-role dashboard into a broader technology job-market intelligence application. The release keeps the scheduled Python pipeline and adds a primary Next.js product interface, wider role and skill coverage, weekly reporting, and a complete Power BI project.

## Included

- Next.js frontend with responsive market, skill, trend, source, quality, certification, practice, and weekly-report views
- Technology coverage across data, software engineering, AI/ML, cloud and platform, database, IT and security, and consulting roles
- Documented job APIs, curated first-run data, Microsoft Learn, freeCodeCamp, GitHub learning paths, and certification sources
- Source confidence labels, isolated connector failures, duplicate URL checks, and pipeline source-run logs
- O*NET skill evidence with BLS wage and growth inputs
- PostgreSQL warehouse with dbt staging, intermediate, dimension, fact, and mart models
- Historical snapshots and weekly rising and declining skill analysis
- FastAPI endpoints, daily local scheduling, Airflow orchestration, and Docker Compose onboarding
- Power BI PBIP/PBIX report, semantic model, DAX measures, and refreshable CSV exports
- GitHub Actions coverage for Python, frontend, Docker, PostgreSQL, and dbt

## Verification

The release was checked with:

```powershell
python -m pip check
python -m unittest discover -s tests
python -m compileall -q api dashboard src tests scripts airflow pipeline.py scheduler.py export_powerbi.py
python pipeline.py
python export_powerbi.py
python scripts/smoke_check.py
npm --prefix frontend audit --omit=dev
npm --prefix frontend run typecheck
npm --prefix frontend run lint
npm --prefix frontend run build
docker compose config --quiet
docker compose -f docker-compose.yml -f docker-compose.airflow.yml --profile airflow config --quiet
docker compose --profile analytics run --rm dbt build
```

Local release results: 48 Python tests passed, the Next.js production build completed, 15 Power BI export tables were generated, and the dbt run completed 76 models and tests with no warnings or errors.

## Boundaries

SkillSync reports directional evidence from the retained sources; it does not claim to represent the entire labor market. Personalized profiles, role-readiness input, career roadmaps, Snowflake loading, and richer skill co-occurrence analysis remain future work.
