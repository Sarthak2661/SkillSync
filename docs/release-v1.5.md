# SkillSync v1.5

SkillSync v1.5 expands the original portfolio release with a tested analytics-engineering layer and more reliable source handling.

## Included

- Multi-source job and learning-resource ingestion with per-source network failure isolation
- Curated first-run defaults with optional live source modes
- Source confidence labels and dashboard source filters
- O*NET software-skill evidence and BLS wage and growth inputs
- PostgreSQL warehouse and dbt staging, intermediate, fact, dimension, and mart models
- dbt not-null, unique, accepted-value, and relationship tests
- Historical skill-demand snapshots and data-quality checks
- Certification paths and GitHub practice-issue recommendations
- FastAPI, Streamlit, Power BI exports, Airflow, and Docker Compose
- Python 3.13 CI tests, smoke checks, exports, and Docker build validation

## Verification

Before tagging the release, run:

```powershell
python -m unittest discover -s tests
python pipeline.py
python export_powerbi.py
python scripts/smoke_check.py
docker compose config --quiet
docker compose -f docker-compose.yml -f docker-compose.airflow.yml --profile airflow config --quiet
```

Create the `v1.5` tag only after CI passes on `main`.