# Local Runbook

This is the short version I use when I want to run the project from a fresh terminal and check that the outputs still look right.

## Docker First Run

Start Docker Desktop, then run this from the project folder:

```powershell
docker compose up --build
```

This starts PostgreSQL, runs the pipeline once, exports Power BI CSV files, starts FastAPI, and starts the Streamlit dashboard.

Open:

- FastAPI docs: `http://127.0.0.1:8000/docs`
- Dashboard: `http://127.0.0.1:8501`

Manual steps you may still need:

- Start Docker Desktop before running Compose.
- Add Adzuna or YouTube API keys to `.env` only if you want those optional live sources.
- If ports `5434`, `8000`, or `8501` are already busy, stop the conflicting local service or change the port mapping in `docker-compose.yml`.
## First Run

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
python pipeline.py
python export_powerbi.py
python scripts\smoke_check.py
```

Expected result: the smoke check should print the latest run ID, job count, course count, skill count, quality warning count, and Power BI CSV count.

## Start The Apps

Use two terminals.

Terminal 1:

```powershell
.\scripts\run_api.ps1
```

Open `http://127.0.0.1:8000/docs`.

Terminal 2:

```powershell
.\scripts\run_dashboard.ps1
```

Open `http://127.0.0.1:8501/`.

If PowerShell blocks scripts, use the `.cmd` files in `scripts/` instead.

## If The Dashboard Shows Only A Few Rows

Check the source modes in `.env`.

For the full local demo, use:

```text
MARKET_INTEL_JOB_SOURCE_MODE=all
MARKET_INTEL_COURSE_SOURCE_MODE=all
MARKET_INTEL_COURSE_SOURCE_LIMIT=200
```

For a faster screenshot-friendly run, use curated jobs with the hybrid course source:

```powershell
$env:MARKET_INTEL_JOB_SOURCE_MODE="curated"
$env:MARKET_INTEL_COURSE_SOURCE_MODE="hybrid"
python pipeline.py
python export_powerbi.py
```

The small `3 jobs / 9 courses` result usually means the pipeline ran with the fallback/sample modes instead of the full source mix.

## If Port 8000 Or 8501 Is Busy

Find the process using the port:

```powershell
netstat -ano | findstr :8000
netstat -ano | findstr :8501
```

Then stop the process by PID:

```powershell
Stop-Process -Id <PID> -Force
```

Restart the API or dashboard after that.

## PostgreSQL Check

The project can run without PostgreSQL, but this is the check I use before saying the warehouse path works.

```powershell
docker compose up -d postgres
$env:MARKET_INTEL_LOAD_TO_POSTGRES="true"
$env:MARKET_INTEL_DB_URL="postgresql://postgres:<your-password>@localhost:5432/job_market_intel"
python pipeline.py
```

After the run, the tables should exist under the `market_intel` schema.

## Airflow Orchestration With Docker

`scheduler.py` is kept as a simple local fallback. For a more realistic portfolio run, use the Airflow DAG.

Start PostgreSQL, Airflow metadata DB, Airflow webserver, and Airflow scheduler:

```powershell
docker compose -f docker-compose.yml -f docker-compose.airflow.yml --profile airflow up --build
```

Open Airflow at `http://localhost:8080`.

Default login:

```text
username: admin
password: admin
```

Enable or trigger the DAG named `skillsync_market_intel_pipeline`.

The DAG tasks are:

1. `ingest` - collects job and course records and writes raw JSONL files.
2. `transform` - creates cleaned jobs, courses, skill summary, trend history, and certification files.
3. `quality_checks` - writes the data quality summary.
4. `export_powerbi_files` - refreshes the CSV files in `powerbi/export/`.
5. `optional_postgresql_load` - loads warehouse tables only when `MARKET_INTEL_LOAD_TO_POSTGRES=true`.

For PostgreSQL loading inside Docker, use this environment value:

```text
MARKET_INTEL_LOAD_TO_POSTGRES=true
```

The Airflow compose file points the warehouse URL at the Docker `postgres` service automatically.
## Quick QA Checklist

- `python -m unittest discover -s tests`
- `python scripts\smoke_check.py`
- `python export_powerbi.py`
- Dashboard opens at `http://127.0.0.1:8501/`
- FastAPI docs open at `http://127.0.0.1:8000/docs`
- `logs/pipeline_runs.csv` has a new timestamped row after each pipeline run
