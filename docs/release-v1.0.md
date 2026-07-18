# SkillSync v1.0

SkillSync v1.0 is the first portfolio release of the job-market intelligence pipeline.

## Included

- Multi-source job and learning-resource ingestion
- Source confidence labels and dashboard source modes
- Skill extraction and O*NET-backed opportunity scoring
- Historical skill-demand snapshots
- Data quality checks and certification recommendations
- PostgreSQL 17 warehouse loading
- FastAPI and Streamlit applications
- Power BI-ready star-schema CSV exports
- Hourly Airflow DAG with a local scheduler fallback
- Python 3.13 and Docker Compose onboarding
- GitHub Actions tests, smoke checks, exports, and Docker build validation

## Verification

Before tagging the release, verify:

```powershell
python -m unittest discover -s tests
python pipeline.py
python export_powerbi.py
python scripts/smoke_check.py
docker compose config --quiet
docker compose -f docker-compose.yml -f docker-compose.airflow.yml --profile airflow config --quiet
```

The release tag should be created only after CI passes on `main`.