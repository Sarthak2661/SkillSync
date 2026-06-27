# Local Runbook

This is the short version I use when I want to run the project from a fresh terminal and check that the outputs still look right.

## First Run

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
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
$env:MARKET_INTEL_DB_URL="postgresql://postgres:postgres@localhost:5432/job_market_intel"
python pipeline.py
```

After the run, the tables should exist under the `market_intel` schema.

## Quick QA Checklist

- `python -m unittest discover -s tests`
- `python scripts\smoke_check.py`
- `python export_powerbi.py`
- Dashboard opens at `http://127.0.0.1:8501/`
- FastAPI docs open at `http://127.0.0.1:8000/docs`
- `logs/pipeline_runs.csv` has a new timestamped row after each pipeline run
