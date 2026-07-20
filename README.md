# SkillSync: Technology Job Market Intelligence

[![CI](https://github.com/Sarthak2661/SkillSync/actions/workflows/ci.yml/badge.svg)](https://github.com/Sarthak2661/SkillSync/actions/workflows/ci.yml)
![Python 3.13](https://img.shields.io/badge/python-3.13-3776AB?logo=python&logoColor=white)
![Docker Ready](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)
![Release v2.0](https://img.shields.io/badge/release-v2.0-2E7D32)

SkillSync is a job-market intelligence application for people exploring technology careers. It compares hiring demand with learning resources across data, software engineering, AI/ML, cloud and platform, database, IT and security, and technology consulting roles.

Behind the product is a Python ETL pipeline that collects job postings and learning resources, extracts skills from the text, validates data quality, stores historical snapshots, and serves the results through a Next.js frontend, FastAPI, optional PostgreSQL tables, and Power BI-ready CSV exports.

See the [v2.0 release notes](docs/release-v2.0.md) for the current release scope and verification checklist.

## Purpose

Technology job descriptions often mix languages, frameworks, platforms, methods, and certifications. The hard part is not finding another course. It is understanding which skills appear in a target role family, whether suitable learning material exists, and which credentials or practice projects deserve attention.

SkillSync turns that question into a small market-intelligence product:

- What skills are employers asking for?
- Which skills have enough courses or videos available?
- Which skills look under-supplied from a learning-resource perspective?
- How does demand change across repeated pipeline runs?
- What should a learner study or certify in next?

## How The Project Works

1. **Ingest**
   The pipeline collects job postings from public APIs and local snapshots, then joins them with Microsoft Learn, freeCodeCamp, GitHub learning paths, and repeatable course catalogs.

2. **Clean**
   Raw records are saved as JSONL, then normalized into analytics-ready job and course CSV files.

3. **Extract Skills**
   A rule-based extractor scans titles, descriptions, subjects, roles, and products for data tools, programming languages, web frameworks, cloud platforms, database systems, AI/ML methods, security concepts, and delivery practices.

4. **Score**
   The project calculates job demand, course supply, skill gap, demand/supply ratio, and a Skill Opportunity Index. Wage and growth inputs use O*NET and BLS occupation references when a skill maps cleanly to a relevant SOC occupation.

5. **Track History**
   Every run writes a `skill_trend_history` snapshot so the dashboard can show skill demand over time.

6. **Validate**
   Quality checks flag missing fields, duplicate records, stale postings, source-domain issues, salary anomalies, and rows where no skills were extracted.

7. **Serve**
   Outputs are available through Next.js, FastAPI, PostgreSQL, and Power BI-ready CSV exports. The earlier Streamlit dashboard remains available as an optional legacy fallback.

## Screenshots

### Overview

![SkillSync Next.js overview dashboard](docs/screenshots/next_dashboard_desktop.png)

### Responsive Overview

![SkillSync Next.js mobile overview](docs/screenshots/next_dashboard_mobile.png)

### Landing Page

![SkillSync landing page](docs/screenshots/next_landing_desktop.png)

### Weekly Market Briefing

![SkillSync weekly market briefing](docs/screenshots/next_weekly_reports.png)

### Skill Trends

![SkillSync trend lab](docs/screenshots/TrendsLab.png)

### Skill Explorer

![SkillSync Next.js skill explorer](docs/screenshots/next_skill_explorer.png)

### Learning And Certification Path

![SkillSync learning and certification path](docs/screenshots/learning_cert_path.png)

### Logs And Data Quality

![SkillSync logs and quality checks](docs/screenshots/logs&quality.png)

### FastAPI Endpoints

![SkillSync FastAPI endpoints](docs/screenshots/FASTAPI%20endpoints.png)

### dbt Lineage

![SkillSync dbt lineage](docs/screenshots/dbt_lineage.png)


## Architecture

```mermaid
flowchart LR
    subgraph Sources
        J1["Official Job APIs"]
        J2["Curated Technology Jobs CSV"]
        J3["HN Who's Hiring via Algolia"]
        C1["YouTube Data API / Fallback"]
        C2["Microsoft Learn Catalog API"]
        C3["Curated Open Course Catalog"]
        C4["freeCodeCamp Curriculum via GitHub"]
        C5["GitHub Learning Paths"]
        K1["Credential Engine / Curated Certifications"]
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
        DBT["dbt Staging + Marts"]
    end

    subgraph Serving
        API["FastAPI Analytics API"]
        WEB["Next.js Product UI"]
        ST["Streamlit Legacy Fallback"]
        PBI["Power BI Export Model"]
    end

    J1 --> I
    J2 --> I
    J3 --> I
    C1 --> I
    C2 --> I
    C3 --> I
    C4 --> I
    C5 --> I
    K1 --> G
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
    API --> WEB
    CSV --> ST
    CSV --> PBI
    CSV --> PG
    PG --> DBT
    DBT --> PBI
```

## What It Does

- Pulls job data from official job APIs, curated sample files, and optional parser-test pages.
- Pulls learning resources from Microsoft Learn, freeCodeCamp's GitHub curriculum index, GitHub learning-path repositories, and YouTube when configured, plus repeatable catalogs of official documentation and open courses.
- Extracts skills such as Python, SQL, Power BI, Airflow, dbt, Snowflake, and AWS.
- Compares job demand with learning-resource supply.
- Grounds skill and wage signals in O*NET-SOC occupation mappings where possible.
- Lets users switch dashboard views between demo-safe data, live sources only, curated market snapshot, and all sources.
- Labels every source with confidence metadata: `live_verified`, `live_broad`, `curated_demo`, `fallback_learning`, or `test_source`.
- Adds O*NET-SOC occupation codes, mapped occupations, wage medians, and outlook fields to the skill ranking table.
- Saves a history row for every pipeline run so trends can be tracked over time.
- Runs basic data quality checks.
- Recommends certifications from a maintained cloud catalog, freeCodeCamp curriculum records, and the optional Credential Engine Registry Search API.
- Finds current good-first-issue and help-wanted work in active GitHub repositories tagged for a selected skill.
- Serves the processed data through Next.js, FastAPI, PostgreSQL, and Power BI exports.

## Project Structure

```text
api/                  FastAPI app
frontend/             React and Next.js product frontend
dashboard/            Legacy Streamlit fallback
dbt/                  PostgreSQL staging, intermediate, dimensions, facts, marts, and tests
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
docker-compose.yml    PostgreSQL, API, dashboard, pipeline, and dbt services
```

## Technology Stack

- Frontend: React 19, Next.js 16, TypeScript, Recharts, and Lucide icons.
- API: FastAPI and pandas-backed analytical helpers.
- Pipeline: Python 3.13, BeautifulSoup, source adapters, ETL transforms, and scheduled snapshots.
- Orchestration: Airflow in Docker, with `scheduler.py` as a lightweight local fallback.
- Storage and modeling: PostgreSQL 17 and dbt.
- Reporting: Power BI-ready star-schema CSV exports.
- Runtime and quality: Docker Compose, GitHub Actions, Python unit tests, ESLint, and TypeScript.

## Docker Quick Start

Start Docker Desktop first, then run:

```powershell
docker compose up --build
```

That starts:

- PostgreSQL 17 at `localhost:5434`
- one bootstrap pipeline run that creates local data files and Power BI CSVs
- FastAPI at `http://127.0.0.1:8000/docs`
- Next.js product UI at `http://127.0.0.1:3000`

No manual database setup is required for the default demo. The API and frontend wait until the first pipeline run has completed.

Optional API keys can be added through your shell or `.env` before starting Docker:

```text
MARKET_INTEL_ADZUNA_APP_ID=
MARKET_INTEL_ADZUNA_APP_KEY=
MARKET_INTEL_YOUTUBE_API_KEY=
```

Stop the stack with:

```powershell
docker compose down
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
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
```

Install the frontend dependencies with Node.js 20.9 or newer:

```powershell
cd frontend
npm.cmd install
cd ..
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

Start FastAPI in one terminal:

```powershell
.\scripts\run_api.ps1
```

Start the Next.js frontend in another terminal:

```powershell
.\scripts\run_dashboard.ps1
```

Open `http://127.0.0.1:3000/`.

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

The default `.env.example` uses curated technology jobs and deterministic learning resources so the first run clears the dashboard sample-size check without depending on live APIs:

```text
MARKET_INTEL_JOB_SOURCE_MODE=curated
MARKET_INTEL_COURSE_SOURCE_MODE=hybrid
MARKET_INTEL_COURSE_SOURCE_LIMIT=200
```

Useful modes:

| Setting | Options |
| --- | --- |
| `MARKET_INTEL_JOB_SOURCE_MODE` | `curated`, `seed`, `adzuna`, `arbeitnow`, `remotive`, `hn`, `job_apis`, `all` |
| `MARKET_INTEL_COURSE_SOURCE_MODE` | `hybrid`, `open_catalog`, `vendor_docs`, `university_open`, `youtube`, `microsoft`, `freecodecamp`, `github_learning`, `official_live`, `all` |
| `MARKET_INTEL_CERTIFICATION_SOURCE_MODE` | `curated`, `freecodecamp`, `credential_engine`, `all` |

`curated` certification mode is the default. It uses the local AWS, Microsoft, and Google Cloud catalog plus a freeCodeCamp curriculum snapshot, so a fresh clone does not need network access. `freecodecamp` verifies tracks against the official GitHub curriculum index. `credential_engine` and `all` query Credential Engine only when `MARKET_INTEL_CREDENTIAL_ENGINE_API_KEY` is set.

Credential Engine's Registry Search API is not anonymous: it requires a Credential Engine account, approval for Graph Search API access, and an API key. The integration is intentionally optional and limited to a small real-time query rather than bulk collection.

More detailed local run notes are in [docs/runbook.md](docs/runbook.md).

## Airflow Orchestration

The project includes a local Airflow DAG for a more realistic data-engineering workflow. `scheduler.py` remains as a simple fallback for users who do not want Docker orchestration.

```powershell
docker compose -f docker-compose.yml -f docker-compose.airflow.yml --profile airflow up --build
```

Open `http://localhost:8080`, log in with `admin` / `admin`, and trigger `skillsync_market_intel_pipeline`.

The DAG runs ingestion, transformation, quality checks, PostgreSQL loading, dbt models/tests, and Power BI export in dependency order.

## Scheduling

Use `scheduler.py` for repeated pipeline runs. It defaults to one run every 1,440 minutes (daily), controlled by `MARKET_INTEL_SCHEDULE_INTERVAL_MINUTES` in `.env`. Logs are written to `logs/scheduler.log`.

For production-style scheduling, run `pipeline.py` through Windows Task Scheduler, cron, or another scheduler of your choice.

## Testing

Run the test suite and smoke check before pushing changes:

```powershell
python -m unittest discover -s tests
python scripts\smoke_check.py
```

The tests cover ingestion, skill extraction, scoring, source confidence, O*NET evidence, data quality, and Power BI star-schema relationships.

Validate the frontend separately:

```powershell
cd frontend
npm.cmd audit --omit=dev
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
```

## FastAPI

Start the API with:

```powershell
.\scripts\run_api.ps1
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation.

Main endpoints include `/health`, `/runs`, `/source-runs`, `/scheduler`, `/kpis`, `/skill-gaps`, `/skill-trends`, `/weekly-reports`, `/jobs`, `/courses`, `/certifications`, `/practice-projects`, `/quality`, and `/sources`. Market endpoints accept `source_view=demo|live|curated|all`.

## Next.js Frontend

Start FastAPI, then start the frontend with:

```powershell
.\scripts\run_dashboard.ps1
```

Open `http://127.0.0.1:3000/`.

Pages include a public landing page, Overview, Skill Explorer and skill detail, Market Trends, Weekly Briefings, Practice Projects, Certifications, Data Quality, Sources, Pipeline Runs, and Methodology. The data-scope control switches between demo-safe, live-only, curated, and all-source views without rewriting pipeline outputs.

The previous Streamlit interface is kept as an explicit fallback:

```powershell
.\scripts\run_streamlit_dashboard.ps1
```

Open `http://127.0.0.1:8501/`. With Docker, use `docker compose --profile legacy up streamlit-dashboard`.

## dbt Analytics Layer

The dbt project turns the pipeline tables into a tested star schema:

- Staging: stg_jobs and stg_courses.
- Intermediate: int_skill_mentions.
- Facts: job skill mentions, course skill coverage, and skill trend history.
- Dimensions: skill, role, location, source, and time.
- Marts: skill opportunity, role-skill demand, and role readiness inputs.

Run it against the Docker PostgreSQL warehouse:

```powershell
docker compose --profile analytics run --rm dbt build
docker compose --profile analytics run --rm dbt docs generate
docker compose --profile analytics run --rm -p 8081:8080 dbt docs serve --host 0.0.0.0 --port 8080
```

The pipeline loader and dbt must point to the same PostgreSQL instance. The default Compose settings already do this. If `MARKET_INTEL_DOCKER_DB_URL` points to PostgreSQL on the Windows host, set `DBT_POSTGRES_HOST`, `DBT_POSTGRES_PORT`, `DBT_POSTGRES_USER`, `DBT_POSTGRES_PASSWORD`, and `DBT_POSTGRES_DB` to that same database before running dbt.

The dbt build covers staging, intermediate models, dimensions, facts, and marts with null, uniqueness, accepted-value, and relationship tests.

## Power BI Dashboard

Run `python export_powerbi.py`, then import the star-schema CSV files from `powerbi/export/` into Power BI Desktop.

Dashboard build instructions, relationships, and DAX measures are documented in [powerbi/README.md](powerbi/README.md).

## GitHub Practice Recommender

On the Practice Projects page, select one skill to find open-source work in recently active repositories tagged with that GitHub topic. Results prefer good first issue, then help wanted, and exclude pull requests.

Public requests work without authentication. For a higher rate limit, add this to your local .env file:

    MARKET_INTEL_GITHUB_TOKEN=your_token_here

The token is optional, read only from the environment, and must not be committed. Responses are cached for 15 minutes. A live issue is a practice lead, not a guarantee that the task is still suitable or maintained.

## Data Quality Checks

The quality layer flags common issues before the dashboard is used, including low sample sizes, unexpected source domains, stale job postings, salary anomalies, duplicate records, reused course URLs, and rows where no skills were extracted.

## Known Limitations

- Live job collection uses documented JSON APIs rather than job-board HTML scraping. API schemas, rate limits, and availability can still change.
- HN Who's Hiring posts are user-authored and semi-structured, so the connector keeps top-level technology-role posts and labels them `live_broad`.
- YouTube uses the YouTube Data API only when `MARKET_INTEL_YOUTUBE_API_KEY` is configured; otherwise it uses local YouTube learning fallback records.
- PostgreSQL loading is optional and depends on Docker or a reachable local PostgreSQL database.
- GitHub issues can be closed or relabeled after retrieval, and unauthenticated API access has lower rate limits.

More notes are in:

- [docs/project_notes.md](docs/project_notes.md)
- [docs/source_notes.md](docs/source_notes.md)
- [docs/methodology.md](docs/methodology.md)
- [docs/runbook.md](docs/runbook.md)
- [docs/roadmap.md](docs/roadmap.md)

## Skill Opportunity Index

The main ranking metric is the Skill Opportunity Index:

```text
Skill Opportunity Index =
Demand Score
+ Growth Score, usually from O*NET occupation outlook
+ Salary Premium Score, usually from O*NET wage medians
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
- Salary premium score uses BLS median wages for mapped occupations, then posting salary ranges or a maintained fallback.
- Growth score uses numeric BLS employment projections for mapped occupations, then a maintained fallback.
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

The pipeline appends summary metadata to `logs/pipeline_runs.csv`. It also writes one row per connector to `logs/source_runs.csv`, recording status, row count, duration, error type, and timestamps. The Pipeline Runs page and `/source-runs` endpoint expose that activity so a failed live source is visible even when the rest of the run succeeds.

## Learning And Certification Path

The dashboard also has a learning page:

- Recommended certifications by skill, provider, provenance, verification date, cost type, target role, and recommendation score.
- Related freeCodeCamp, GitHub learning-path, YouTube, Microsoft Learn, vendor-doc, university, and open-course resources.
- Market context for selected skills, including opportunity index, job demand, course supply, and target roles.

This page is meant to answer: "If this skill looks useful, what should I study or certify in next?"

## Reference data

The extraction taxonomy is project-defined. Exact technology matches are checked against O*NET Software Skills 30.3 and separated from broader occupation mappings. BLS supplies wage and employment-projection inputs. See [docs/methodology.md](docs/methodology.md) for definitions, limitations, source links, and attribution.

## Roadmap

Planned work is tracked in [docs/roadmap.md](docs/roadmap.md).
