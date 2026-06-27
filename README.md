# SkillSync: Job Market Intelligence Dashboard

SkillSync is a Python ETL project for comparing job-market skills with course and video resources.

The project collects job postings and learning resources, extracts skills from the text, and turns the results into CSV outputs, a Streamlit dashboard, FastAPI endpoints, optional PostgreSQL tables, and Power BI-ready files.

## Real-World Problem

People trying to enter data analyst, data engineering, or data science roles often see long lists of skills: SQL, Python, Power BI, Airflow, dbt, Snowflake, AWS, and many more. The hard part is not finding learning resources. The hard part is knowing which skills are actually showing up in job postings, whether enough learning material exists for those skills, and which certifications might be worth considering.

SkillSync treats that as a small market-intelligence problem:

- What skills are employers asking for?
- Which skills have enough courses or videos available?
- Which skills look under-supplied from a learning-resource perspective?
- How does demand change across repeated pipeline runs?
- What should a learner study or certify in next?

## How The Project Works

1. **Ingest**
   The pipeline collects job postings from public/sample job sources and learning resources from Microsoft Learn, YouTube/fallback records, vendor docs, open course catalogs, and university/open learning pages.

2. **Clean**
   Raw records are saved as JSONL, then normalized into analytics-ready job and course CSV files.

3. **Extract Skills**
   A rule-based skill extractor scans titles, descriptions, subjects, roles, and products for tools and skills such as Python, SQL, Power BI, Airflow, dbt, Snowflake, AWS, Azure, and machine learning.

4. **Score**
   The project calculates job demand, course supply, skill gap, demand/supply ratio, and a Skill Opportunity Index.

5. **Track History**
   Every run writes a `skill_trend_history` snapshot so the dashboard can show skill demand over time.

6. **Validate**
   Quality checks flag missing fields, duplicate records, stale postings, source-domain issues, salary anomalies, and rows where no skills were extracted.

7. **Serve**
   Outputs are available through Streamlit, FastAPI, PostgreSQL, and Power BI-ready CSV exports.

## Screenshots

### Overview

![SkillSync overview dashboard](docs/screenshots/dashboard_overview.png)

### Skill Trends

![SkillSync trend lab](docs/screenshots/TrendsLab.png)

### Skill Explorer

![SkillSync skill explorer](docs/screenshots/skills_explorer.png)

### Learning And Certification Path

![SkillSync learning and certification path](docs/screenshots/learning_cert_path.png)

### Logs And Data Quality

![SkillSync logs and quality checks](docs/screenshots/logs&quality.png)

### FastAPI Endpoints

![SkillSync FastAPI endpoints](docs/screenshots/FASTAPI%20endpoints.png)

## Google XYZ Resume Framing

Google's XYZ resume format is: **Accomplished X, as measured by Y, by doing Z.**

For this project:

> Built a job-market skill intelligence pipeline, identifying 42 tracked skills across 156 job postings and 41 learning resources, by scraping multi-source job/course data, extracting skills with Python, validating data quality, and serving results through Streamlit, FastAPI, PostgreSQL, and Power BI exports.

Shorter version:

> Built a scheduled ETL dashboard for labor-market skill analysis, tracking 42 skills and historical demand snapshots, by ingesting job/course data, applying quality checks, and publishing analytics through FastAPI, Streamlit, PostgreSQL, and Power BI.

## Architecture

```mermaid
flowchart LR
    subgraph Sources
        J1["Y Combinator Jobs"]
        J2["Curated Data-Role Jobs CSV"]
        J3["Real Python Fake Jobs HTML"]
        C1["YouTube Data API / Fallback"]
        C2["Microsoft Learn Catalog API"]
        C3["Curated Open Course Catalog"]
    end

    subgraph Pipeline
        I["Ingestion Connectors"]
        R["Raw JSONL Extracts"]
        T["Transform + Skill Extraction"]
        Q["Data Quality + Fact Checks"]
        G["Skill Gap + Opportunity Summary"]
        H["Skill Trend History Snapshots"]
    end

    subgraph Storage
        CSV["Processed CSV Snapshots"]
        PG["PostgreSQL Warehouse"]
    end

    subgraph Serving
        API["FastAPI Analytics API"]
        ST["Streamlit Dashboard"]
        PBI["Power BI Export Model"]
    end

    J1 --> I
    J2 --> I
    J3 --> I
    C1 --> I
    C2 --> I
    C3 --> I
    I --> R
    R --> T
    T --> Q
    T --> G
    T --> H
    Q --> CSV
    G --> CSV
    H --> CSV
    T --> CSV
    CSV --> API
    CSV --> ST
    CSV --> PBI
    CSV --> PG
```

## What It Does

- Pulls job data from sample files and public job pages.
- Pulls learning resources from Microsoft Learn, YouTube, and small maintained catalogs.
- Extracts skills such as Python, SQL, Power BI, Airflow, dbt, Snowflake, and AWS.
- Compares job demand with learning-resource supply.
- Saves a history row for every pipeline run so trends can be tracked over time.
- Runs basic data quality checks.
- Recommends certifications for selected skills.
- Serves the processed data through Streamlit, FastAPI, PostgreSQL, and Power BI exports.

## Project Structure

```text
api/                  FastAPI app
dashboard/            Streamlit dashboard
powerbi/              Power BI model and dashboard handoff
docs/                 Project notes, source notes, runbook, roadmap, screenshots
scripts/              Small local run/check scripts
src/analytics/        API and Power BI analytical model helpers
src/config/           Environment-based settings
src/etl/              File IO and transformations
src/ingestion/        Source connectors
src/quality/          Data quality checks
src/warehouse/        PostgreSQL loader
pipeline.py           One-time ETL run
scheduler.py          Recurring ETL scheduler
export_powerbi.py     Power BI CSV model export
docker-compose.yml    Local PostgreSQL service
```

## Quickstart

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python pipeline.py
```

By default, the project uses sample/local sources so it can run without extra setup. Use seed mode if you only want a quick smoke test.

Recommended local run:

```powershell
$env:MARKET_INTEL_JOB_SOURCE_MODE="curated"
$env:MARKET_INTEL_COURSE_SOURCE_MODE="hybrid"
$env:MARKET_INTEL_COURSE_SOURCE_LIMIT="50"
python pipeline.py
python export_powerbi.py
```

This run is better for screenshots because the sample jobs have full data-role descriptions. The fake-jobs site is still useful for testing the scraper, but most of those jobs are not data roles.

## Job Source Modes

Run the sample data-role job source:

```powershell
$env:MARKET_INTEL_JOB_SOURCE_MODE="curated"
python pipeline.py
```

Run the small offline seed source:

```powershell
$env:MARKET_INTEL_JOB_SOURCE_MODE="seed"
python pipeline.py
```

Run the live job scraper:

```powershell
$env:MARKET_INTEL_JOB_SOURCE_MODE="realpython"
python pipeline.py
```

Run the Y Combinator Jobs scraper:

```powershell
$env:MARKET_INTEL_JOB_SOURCE_MODE="yc"
python pipeline.py
```

Run all job sources:

```powershell
$env:MARKET_INTEL_JOB_SOURCE_MODE="all"
python pipeline.py
```

Run the hybrid course connector:

```powershell
$env:MARKET_INTEL_COURSE_SOURCE_MODE="hybrid"
python pipeline.py
```

Run the open-course connector:

```powershell
$env:MARKET_INTEL_COURSE_SOURCE_MODE="open_catalog"
python pipeline.py
```

Run the vendor documentation course connector:

```powershell
$env:MARKET_INTEL_COURSE_SOURCE_MODE="vendor_docs"
python pipeline.py
```

Run the university/open learning connector:

```powershell
$env:MARKET_INTEL_COURSE_SOURCE_MODE="university_open"
python pipeline.py
```

Run the YouTube learning-video connector:

```powershell
$env:MARKET_INTEL_COURSE_SOURCE_MODE="youtube"
$env:MARKET_INTEL_YOUTUBE_API_KEY="your_api_key_optional"
python pipeline.py
```

If no YouTube API key is set, the connector uses local fallback records so the project still runs after cloning.

Run the live Microsoft Learn course connector:

```powershell
$env:MARKET_INTEL_COURSE_SOURCE_MODE="microsoft"
python pipeline.py
```

Run all course sources:

```powershell
$env:MARKET_INTEL_COURSE_SOURCE_MODE="all"
python pipeline.py
```

Run the full source mix:

```powershell
$env:MARKET_INTEL_JOB_SOURCE_MODE="all"
$env:MARKET_INTEL_COURSE_SOURCE_MODE="all"
$env:MARKET_INTEL_COURSE_SOURCE_LIMIT="25"
python pipeline.py
python export_powerbi.py
```

Run sample jobs with live/hybrid courses:

```powershell
$env:MARKET_INTEL_JOB_SOURCE_MODE="curated"
$env:MARKET_INTEL_COURSE_SOURCE_MODE="hybrid"
python pipeline.py
```

Run Microsoft Learn plus the open-course catalog:

```powershell
$env:MARKET_INTEL_COURSE_SOURCE_MODE="microsoft_open"
$env:MARKET_INTEL_COURSE_SOURCE_LIMIT="50"
python pipeline.py
```

Run the live job scraper with Microsoft Learn:

```powershell
$env:MARKET_INTEL_JOB_SOURCE_MODE="realpython"
$env:MARKET_INTEL_COURSE_SOURCE_MODE="microsoft"
$env:MARKET_INTEL_COURSE_SOURCE_LIMIT="50"
python pipeline.py
```

## Scheduling

Run the scheduler locally:

```powershell
$env:MARKET_INTEL_JOB_SOURCE_MODE="curated"
$env:MARKET_INTEL_COURSE_SOURCE_MODE="microsoft"
$env:MARKET_INTEL_SCHEDULE_INTERVAL_MINUTES="60"
python scheduler.py
```

The scheduler writes logs to `logs/scheduler.log`.

For Windows Task Scheduler, create a task with:

- Program: `C:\path\to\repo\.venv\Scripts\python.exe`
- Arguments: `pipeline.py`
- Start in: `C:\path\to\repo`
- Trigger: hourly, daily, or your preferred cadence

For cron on macOS/Linux:

```cron
0 * * * * cd /path/to/repo && /path/to/repo/.venv/bin/python pipeline.py >> logs/cron.log 2>&1
```

## PostgreSQL Warehouse

Start a local PostgreSQL database:

```powershell
docker compose up -d postgres
```

Enable warehouse loading:

```powershell
$env:MARKET_INTEL_DB_URL="postgresql://postgres:postgres@localhost:5432/job_market_intel"
$env:MARKET_INTEL_LOAD_TO_POSTGRES="true"
python pipeline.py
```

Warehouse tables are created under the `market_intel` schema:

- `market_intel.job_postings`
- `market_intel.course_listings`
- `market_intel.skill_gap_summary`
- `market_intel.skill_trend_history`
- `market_intel.certification_recommendations`
- `market_intel.quality_checks`

Each table includes `run_id`, so repeated runs append snapshots instead of replacing historical results.

## Testing

Run the parser and skill-extraction tests:

```powershell
python -m unittest discover -s tests
```

Run a quick output check after the pipeline:

```powershell
python scripts/smoke_check.py
```

The test suite currently checks:

- RealPython job-card parsing.
- Y Combinator job-card parsing, including salary and location extraction.
- YouTube fallback learning-source records.
- Core skill extraction for Python, SQL, ETL, Airflow, dbt, Power BI, and Data Quality.

To verify PostgreSQL loading, install Docker Desktop, then run:

```powershell
docker compose up -d postgres
$env:MARKET_INTEL_LOAD_TO_POSTGRES="true"
$env:MARKET_INTEL_DB_URL="postgresql://postgres:postgres@localhost:5432/job_market_intel"
python pipeline.py
```

## FastAPI

Start the API:

```powershell
uvicorn api.main:app --reload
```

Or use the helper script on Windows:

```powershell
.\scripts\run_api.ps1
```

If PowerShell blocks scripts on your machine, use:

```powershell
.\scripts\run_api.cmd
```

Open:

- API root: `http://127.0.0.1:8000/`
- API docs: `http://127.0.0.1:8000/docs`

Useful endpoints:

- `/health`
- `/runs/latest`
- `/kpis`
- `/skill-gaps`
- `/skill-trends`
- `/skills/{skill}`
- `/jobs`
- `/courses`
- `/certifications`
- `/quality`
- `/sources`
- `/datasets`

Example:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/kpis"
Invoke-RestMethod "http://127.0.0.1:8000/skills/Python"
Invoke-RestMethod "http://127.0.0.1:8000/skill-trends?skill=Python"
```

## Streamlit Dashboard

```powershell
streamlit run dashboard/app.py
```

Or use the helper script on Windows:

```powershell
.\scripts\run_dashboard.ps1
```

If PowerShell blocks scripts on your machine, use:

```powershell
.\scripts\run_dashboard.cmd
```

Dashboard pages:

- `Overview`: KPIs, opportunity ranking, demand vs course supply, and target roles.
- `Trend Lab`: historical skill demand lines, run history, and weekly trend view after 7+ days of snapshots.
- `Skills Explorer`: skill-level drilldown into jobs, courses, and score inputs.
- `Learning & Certification Path`: course/video resources plus free and paid certification recommendations by skill.
- `Logs & Quality`: timestamped pipeline runs, scheduler log tail, and data quality checks.
- `Guide`: dashboard interpretation and data sources.

## Power BI Dashboard

Generate Power BI-ready tables:

```powershell
python export_powerbi.py
```

Import the CSV files from `powerbi/export/` into Power BI Desktop.

Dashboard build instructions, relationships, and DAX measures are documented in [powerbi/README.md](powerbi/README.md).

## Data Quality Checks

The quality layer produces a structured `quality_summary` table with:

- `dataset`
- `check_name`
- `status`
- `severity`
- `records_checked`
- `failed_count`
- `message`

These checks catch common issues before the dashboard is used. For example, the pipeline flags low sample sizes, unexpected source domains, stale job postings, and rows where no skills were extracted.

## Known Limitations

- Y Combinator Jobs and RealPython Fake Jobs are useful public sources, but they include broad engineering or tutorial job postings that are not always data-specific. Because of that, job skill coverage can be lower than the sample data-role source.
- Live websites can change their HTML structure or access rules. The project includes sample/fallback sources so it can still run when a public source changes.
- YouTube uses the YouTube Data API only when `MARKET_INTEL_YOUTUBE_API_KEY` is configured; otherwise it uses local YouTube learning fallback records.
- PostgreSQL loading is optional and depends on Docker or a reachable local PostgreSQL database.

More notes are in:

- [docs/project_notes.md](docs/project_notes.md)
- [docs/source_notes.md](docs/source_notes.md)
- [docs/runbook.md](docs/runbook.md)
- [docs/roadmap.md](docs/roadmap.md)

## Skill Opportunity Index

The main ranking metric is the Skill Opportunity Index:

```text
Skill Opportunity Index =
Demand Score
+ Growth Score
+ Salary Premium Score
- Course Supply Score
- Saturation Score
```

The output is scaled from 0 to 100:

```text
50
+ 0.35 * demand_score
+ 0.25 * growth_score
+ 0.25 * salary_premium_score
- 0.20 * course_supply_score
- 0.15 * saturation_score
```

Inputs:

- `demand_score`: calculated from job postings for the current run.
- `course_supply_score`: calculated from course listings for the current run.
- `salary_premium_score`: calculated from salary ranges when available; otherwise it uses a simple default for that skill.
- `growth_score`: a hand-maintained market signal until there is enough historical data for a better estimate.
- `saturation_score`: a rough signal for whether the skill is crowded or more of a basic requirement.

Labels:

- `High-value`: worth paying attention to.
- `Good bet`: useful and still has room in the market.
- `Balanced`: useful, but not clearly under-supplied.
- `Lower priority`: weaker demand, high saturation, or course-heavy.

The reason for this metric is simple: the most common skill is not always the best skill to learn next. A high-demand skill with plenty of courses may be less interesting than a growing skill with fewer learning resources.

## Skill Trend History

Every pipeline run writes a `skill_trend_history` snapshot with:

- `run_id`
- `run_timestamp`
- `source_name`
- `skill`
- `job_count`
- `course_count`
- `salary_min_avg`
- `salary_max_avg`
- `location`
- `role_category`

After multiple runs, the dashboard and API can answer trend questions such as:

- Python demand over time.
- SQL demand over time.
- Power BI vs Tableau demand.
- AWS vs Azure vs GCP cloud demand.
- GenAI, LLM, Responsible AI, or NLP skill growth.
- Airflow, dbt, Spark, and Databricks demand by role category.

The trend table is split by `location` and `role_category`, so Power BI can compare skill demand across markets and job tracks instead of showing one global count.

The pipeline also appends run metadata to `logs/pipeline_runs.csv`, including the run timestamp, record counts, trend-row count, and top opportunity skill. The dashboard's `Logs & Quality` page reads this file so scheduled refreshes can be audited.

## Learning And Certification Path

The dashboard also has a learning page:

- Recommended certifications by skill, provider, level, cost type, target role, and recommendation score.
- Related YouTube, Microsoft Learn, vendor-doc, university, and open-course resources.
- Market context for selected skills, including opportunity index, job demand, course supply, and target roles.

This page is meant to answer: "If this skill looks useful, what should I study or certify in next?"

## Resume Notes

Example bullet:

> Built a scheduled Python ETL pipeline that ingests job postings and course listings, extracts technical skills, validates data quality, loads analytics-ready outputs into PostgreSQL, and powers FastAPI, Streamlit, and Power BI dashboards for skill-gap analysis.

Version that mentions historical snapshots:

> Built a scheduled labor-market intelligence pipeline that captures historical snapshots of job and course data, tracks skill demand trends over time, computes a Skill Opportunity Index, validates data quality, and serves analytics through PostgreSQL, FastAPI, Streamlit, and Power BI.

## Next Improvements

- Add more real job sources with richer job descriptions.
- Add star-schema warehouse views for Power BI direct query.
- Add forecasting for skill demand trends after multiple scheduled runs.
- Add clustering for role/skill group discovery.
- Tighten source filters so broad engineering jobs do not dilute data-role insights.


