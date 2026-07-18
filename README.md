# SkillSync: Job Market Intelligence Dashboard

SkillSync is a Python ETL project for comparing job-market skills with course and video resources.

The project collects job postings and learning resources, extracts skills from the text, and turns the results into CSV outputs, a Streamlit dashboard, FastAPI endpoints, optional PostgreSQL tables, and Power BI-ready files.

## Purpose

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

## Local Setup

Clone the repository and open it in VS Code:

```powershell
git clone https://github.com/Sarthak2661/SkillSync.git
cd SkillSync
code .
```

Create a virtual environment and install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Run the pipeline once:

```powershell
python pipeline.py
```

Export the Power BI CSV model:

```powershell
python export_powerbi.py
```

Run a quick check that the latest output is readable:

```powershell
python scripts\smoke_check.py
```

Start the dashboard:

```powershell
.\scripts\run_dashboard.ps1
```

Open `http://127.0.0.1:8501/`.

Start the API in a second terminal:

```powershell
.\scripts\run_api.ps1
```

Open `http://127.0.0.1:8000/docs`.

If PowerShell blocks scripts on your machine, use the `.cmd` files in `scripts/` instead.

## Optional PostgreSQL Loading

The project runs without PostgreSQL by default. To load pipeline outputs into a local PostgreSQL warehouse, update `.env`:

```text
MARKET_INTEL_LOAD_TO_POSTGRES=true
MARKET_INTEL_DB_URL=postgresql://postgres:<your-password>@localhost:5432/job_market_intel
```

Then run:

```powershell
python pipeline.py
```

The loader creates tables under the `market_intel` schema.

If you prefer Docker, start the included PostgreSQL service first:

```powershell
docker compose up -d postgres
```

The Docker database uses the credentials in `docker-compose.yml`.

## Source Modes

The default `.env.example` runs the full source mix. For a faster local demo, change these values in `.env`:

```text
MARKET_INTEL_JOB_SOURCE_MODE=curated
MARKET_INTEL_COURSE_SOURCE_MODE=hybrid
MARKET_INTEL_COURSE_SOURCE_LIMIT=50
```

Useful modes:

| Setting | Options |
| --- | --- |
| `MARKET_INTEL_JOB_SOURCE_MODE` | `curated`, `seed`, `realpython`, `yc`, `all` |
| `MARKET_INTEL_COURSE_SOURCE_MODE` | `hybrid`, `open_catalog`, `vendor_docs`, `university_open`, `youtube`, `microsoft`, `microsoft_open`, `all` |

More detailed local run notes are in [docs/runbook.md](docs/runbook.md).

## Scheduling

Use `scheduler.py` for repeated pipeline runs. The interval is controlled by `MARKET_INTEL_SCHEDULE_INTERVAL_MINUTES` in `.env`, and logs are written to `logs/scheduler.log`.

For production-style scheduling, run `pipeline.py` through Windows Task Scheduler, cron, or another scheduler of your choice.

## Testing

Run the test suite and smoke check before pushing changes:

```powershell
python -m unittest discover -s tests
python scripts\smoke_check.py
```

The tests cover parser behavior, YouTube fallback records, and core skill extraction.

## FastAPI

Start the API with:

```powershell
.\scripts\run_api.ps1
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation.

Main endpoints include `/health`, `/kpis`, `/skill-gaps`, `/skill-trends`, `/jobs`, `/courses`, `/certifications`, `/quality`, and `/sources`.

## Streamlit Dashboard

Start the dashboard with:

```powershell
.\scripts\run_dashboard.ps1
```

Open `http://127.0.0.1:8501/`.

Dashboard pages include Overview, Trend Lab, Skills Explorer, Learning & Certification Path, Logs & Quality, and Guide.

## Power BI Dashboard

Run `python export_powerbi.py`, then import the CSV files from `powerbi/export/` into Power BI Desktop.

Dashboard build instructions, relationships, and DAX measures are documented in [powerbi/README.md](powerbi/README.md).

## Data Quality Checks

The quality layer flags common issues before the dashboard is used, including low sample sizes, unexpected source domains, stale job postings, salary anomalies, duplicate records, and rows where no skills were extracted.

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


## Next Improvements

- Add more real job sources with richer job descriptions.
- Add star-schema warehouse views for Power BI direct query.
- Add forecasting for skill demand trends after multiple scheduled runs.
- Add clustering for role/skill group discovery.
- Tighten source filters so broad engineering jobs do not dilute data-role insights.


