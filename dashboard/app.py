from __future__ import annotations

import sys
import re
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.etl.io import read_all_dataframes, read_latest_dataframe  # noqa: E402
from src.etl.transform import build_skill_gap_summary  # noqa: E402
from src.analytics.certifications import build_certification_recommendations  # noqa: E402
from src.analytics.github_practice import recommend_practice_projects  # noqa: E402
from src.analytics.source_confidence import (  # noqa: E402
    SOURCE_VIEW_OPTIONS,
    add_source_confidence,
    confidence_for_source,
    filter_by_sources,
    filter_trends,
)
from src.config.settings import settings  # noqa: E402


APP_TITLE = "SkillSync: Job Market Intelligence Dashboard"


st.set_page_config(page_title="SkillSync", layout="wide", page_icon="SS")


@st.cache_data(ttl=60)
def load_data() -> dict[str, pd.DataFrame]:
    return {
        "jobs": add_source_confidence(read_latest_dataframe("job_postings_clean")),
        "courses": add_source_confidence(read_latest_dataframe("course_listings_clean")),
        "gaps": read_latest_dataframe("skill_gap_summary"),
        "quality": read_latest_dataframe("quality_summary"),
        "certifications": read_latest_dataframe("certification_recommendations"),
        "trends": read_all_dataframes("skill_trend_history"),
        "runs": read_run_log(),
    }


def read_run_log() -> pd.DataFrame:
    path = PROJECT_ROOT / "logs" / "pipeline_runs.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def ensure_columns(df: pd.DataFrame, defaults: dict[str, object]) -> pd.DataFrame:
    out = df.copy()
    for column, value in defaults.items():
        if column not in out:
            out[column] = value
    return out


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ss-bg: #0b0f14;
            --ss-bg-soft: #111820;
            --ss-panel: #f8fafc;
            --ss-panel-2: #eef3f7;
            --ss-text: #101827;
            --ss-muted: #667085;
            --ss-line: #d8e0e8;
            --ss-teal: #14b8a6;
            --ss-coral: #f97362;
            --ss-gold: #d89f18;
        }

        @keyframes ssFadeUp {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes ssAccent {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .stApp {
            background:
                linear-gradient(135deg, rgba(20, 184, 166, .08), transparent 32%),
                linear-gradient(180deg, #0b0f14 0%, #10161d 52%, #0d1117 100%);
            color: #f8fafc;
        }

        .block-container {
            max-width: 1240px;
            padding-top: 1.25rem;
            padding-bottom: 3rem;
            animation: ssFadeUp .45s ease-out both;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #121821 0%, #0d131a 100%);
            border-right: 1px solid rgba(216, 224, 232, .12);
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1.1rem;
        }

        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] span {
            color: #dbe5ee;
        }

        section[data-testid="stSidebar"] h3 {
            color: #f8fafc;
            font-size: .82rem;
            text-transform: uppercase;
            letter-spacing: .08em;
            margin-top: 1rem;
        }

        section[data-testid="stSidebar"] [role="radiogroup"] label {
            border-radius: 8px;
            padding: .18rem .25rem;
            transition: background .2s ease, transform .2s ease;
        }

        section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
            background: rgba(20, 184, 166, .12);
            transform: translateX(2px);
        }

        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background: #0b1118;
            border: 1px solid rgba(216, 224, 232, .16);
            border-radius: 8px;
            box-shadow: none;
        }

        section[data-testid="stSidebar"] div[data-baseweb="tag"] {
            background: #1f2933;
            border: 1px solid rgba(20, 184, 166, .35);
            color: #e8f7f5;
            border-radius: 8px;
        }

        section[data-testid="stSidebar"] div[data-baseweb="tag"]:nth-of-type(2n) {
            border-color: rgba(249, 115, 98, .45);
        }

        section[data-testid="stSidebar"] [data-testid="stSlider"] div[role="slider"] {
            background-color: var(--ss-teal);
            border-color: #a7f3d0;
        }

        .skillsync-hero {
            text-align: center;
            padding: 1.4rem 1rem 1.15rem;
            border-bottom: 1px solid rgba(216, 224, 232, .22);
            margin-bottom: 1.15rem;
            position: relative;
        }

        .skillsync-hero::after {
            content: "";
            display: block;
            width: 180px;
            height: 3px;
            margin: 1rem auto 0;
            border-radius: 8px;
            background: linear-gradient(90deg, var(--ss-teal), var(--ss-gold), var(--ss-coral));
            background-size: 200% 200%;
            animation: ssAccent 7s ease infinite;
        }

        .skillsync-title {
            font-size: 2.9rem;
            line-height: 1.08;
            font-weight: 800;
            color: #f8fafc;
            margin: 0;
            letter-spacing: 0;
        }

        .skillsync-subtitle {
            color: #b9c7d6;
            font-size: 1rem;
            margin-top: .55rem;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, #ffffff 0%, #f6f9fb 100%);
            border: 1px solid var(--ss-line);
            border-radius: 8px;
            padding: 1.05rem 1.15rem;
            box-shadow: 0 14px 30px rgba(2, 6, 23, .24);
            min-height: 96px;
            transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
            animation: ssFadeUp .5s ease-out both;
        }

        div[data-testid="stMetric"]:hover {
            transform: translateY(-3px);
            border-color: rgba(20, 184, 166, .5);
            box-shadow: 0 18px 36px rgba(2, 6, 23, .3);
        }

        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"],
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] p {
            color: var(--ss-muted) !important;
            font-weight: 700 !important;
            opacity: 1 !important;
        }

        div[data-testid="stMetric"] [data-testid="stMetricValue"],
        div[data-testid="stMetric"] [data-testid="stMetricValue"] div {
            color: var(--ss-text) !important;
            font-weight: 800 !important;
            opacity: 1 !important;
        }

        div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
            color: var(--ss-teal) !important;
        }

        .insight-strip {
            background: rgba(248, 250, 252, .98);
            border: 1px solid var(--ss-line);
            border-left: 4px solid var(--ss-teal);
            border-radius: 8px;
            padding: .9rem 1rem;
            margin: .65rem 0 1.1rem;
            color: #243244;
            box-shadow: 0 10px 24px rgba(2, 6, 23, .16);
            animation: ssFadeUp .52s ease-out both;
        }

        .section-label {
            font-size: .8rem;
            color: #b9c7d6;
            text-transform: uppercase;
            letter-spacing: .06em;
            font-weight: 700;
            margin-bottom: .35rem;
        }

        .soft-panel {
            background: linear-gradient(180deg, rgba(248, 250, 252, .99), rgba(239, 245, 248, .99));
            border: 1px solid var(--ss-line);
            border-radius: 8px;
            padding: 1.05rem 1.15rem;
            margin: 1rem 0 1.25rem;
            color: #1f2a37;
            box-shadow: 0 12px 28px rgba(2, 6, 23, .18);
            animation: ssFadeUp .55s ease-out both;
        }

        .soft-panel h4 {
            color: var(--ss-text);
            margin: 0 0 .35rem 0;
        }

        .soft-panel p, .soft-panel li {
            color: #334155;
        }

        .section-spacer { height: 1.25rem; }

        div[data-testid="stDataFrame"] {
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid rgba(216, 224, 232, .18);
            box-shadow: 0 12px 28px rgba(2, 6, 23, .18);
        }

        div[data-testid="stAlert"] {
            border-radius: 8px;
        }

        button[kind="secondary"], button[data-testid="baseButton-secondary"] {
            border-radius: 8px;
            border-color: rgba(20, 184, 166, .35);
        }

        @media (max-width: 760px) {
            .skillsync-title { font-size: 2.1rem; }
            .block-container { padding-left: 1rem; padding-right: 1rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        f"""
        <div class="skillsync-hero">
            <h1 class="skillsync-title">{APP_TITLE}</h1>
            <div class="skillsync-subtitle">
                Job skills, learning resources, opportunity scores, and run history.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def filtered_frames(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    gaps = data["gaps"]
    trends = data["trends"]
    jobs = data["jobs"]
    courses = data["courses"]

    with st.sidebar:
        st.markdown("### Data Scope")
        selected_source_view = st.radio(
            "Source view",
            list(SOURCE_VIEW_OPTIONS.keys()),
            index=list(SOURCE_VIEW_OPTIONS.keys()).index("All sources"),
        )
        st.caption(SOURCE_VIEW_OPTIONS[selected_source_view]["description"])

    source_config = SOURCE_VIEW_OPTIONS[selected_source_view]
    filtered_jobs = filter_by_sources(jobs, source_config["jobs"])
    filtered_courses = filter_by_sources(courses, source_config["courses"])

    if selected_source_view == "All sources":
        filtered_gaps = gaps.copy()
    elif filtered_jobs.empty and filtered_courses.empty:
        filtered_gaps = gaps.iloc[0:0].copy()
    else:
        filtered_gaps = build_skill_gap_summary(filtered_jobs, filtered_courses)
        filtered_gaps = ensure_columns(
            filtered_gaps,
            {
                "opportunity_index": 0,
                "opportunity_label": "Unknown",
                "target_job_roles": "Data Analyst | Data Engineer | Data Scientist",
            },
        )

    categories = sorted(filtered_gaps["category"].dropna().unique()) if "category" in filtered_gaps else []
    labels = sorted(filtered_gaps["opportunity_label"].dropna().unique()) if "opportunity_label" in filtered_gaps else []

    with st.sidebar:
        st.markdown("### Filters")
        selected_categories = st.multiselect("Skill categories", categories, default=categories)
        selected_labels = st.multiselect("Opportunity labels", labels, default=labels)
        min_opportunity = st.slider("Minimum opportunity index", 0, 100, 0)

    if selected_categories and "category" in filtered_gaps:
        filtered_gaps = filtered_gaps[filtered_gaps["category"].isin(selected_categories)]
    if selected_labels and "opportunity_label" in filtered_gaps:
        filtered_gaps = filtered_gaps[filtered_gaps["opportunity_label"].isin(selected_labels)]
    if "opportunity_index" in filtered_gaps:
        filtered_gaps = filtered_gaps[pd.to_numeric(filtered_gaps["opportunity_index"], errors="coerce").fillna(0) >= min_opportunity]

    selected_skills = set(filtered_gaps["skill"]) if "skill" in filtered_gaps else set()
    filtered_trends = filter_trends(trends, source_config["jobs"], selected_skills)
    filtered_certifications = build_certification_recommendations(filtered_gaps) if not filtered_gaps.empty else data["certifications"].iloc[0:0].copy()

    return {
        "jobs": filtered_jobs,
        "courses": filtered_courses,
        "gaps": filtered_gaps,
        "quality": data["quality"],
        "certifications": filtered_certifications,
        "trends": filtered_trends,
        "runs": data["runs"],
        "source_view": selected_source_view,
        "source_view_description": source_config["description"],
    }


def source_catalog() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "type": "Jobs",
                "source": "Adzuna Jobs API",
                "mode": "adzuna",
                "source_confidence": "live_verified",
                "site_or_file": "https://api.adzuna.com/v1/api/jobs/",
                "use": "Official job API. Requires free app id/key in .env.",
            },
            {
                "type": "Jobs",
                "source": "Arbeitnow Job API",
                "mode": "arbeitnow",
                "source_confidence": "live_verified",
                "site_or_file": "https://www.arbeitnow.com/api/job-board-api",
                "use": "Public no-key JSON job API.",
            },
            {
                "type": "Jobs",
                "source": "Remotive Jobs API",
                "mode": "remotive",
                "source_confidence": "live_verified",
                "site_or_file": "https://remotive.com/api/remote-jobs",
                "use": "Official remote-jobs JSON API.",
            },
            {
                "type": "Jobs",
                "source": "Sample Data Jobs",
                "mode": "curated",
                "source_confidence": "curated_demo",
                "site_or_file": "data/sample/curated_data_jobs.csv",
                "use": "Local jobs with full data-role descriptions.",
            },
            {
                "type": "Jobs",
                "source": "Startup Data Jobs",
                "mode": "startup",
                "source_confidence": "curated_demo",
                "site_or_file": "src/ingestion/job_sources.py",
                "use": "Small startup-style data job feed.",
            },
            {
                "type": "Jobs",
                "source": "Enterprise Analytics Jobs",
                "mode": "enterprise",
                "source_confidence": "curated_demo",
                "site_or_file": "src/ingestion/job_sources.py",
                "use": "Small enterprise BI and cloud analytics feed.",
            },
            {
                "type": "Jobs",
                "source": "Y Combinator Jobs",
                "mode": "yc",
                "source_confidence": "live_broad",
                "site_or_file": "https://www.ycombinator.com/jobs",
                "use": "Optional legacy HTML scraper. Real but broad; not used in the default all-source mix.",
            },
            {
                "type": "Jobs",
                "source": "Real Python Fake Jobs",
                "mode": "realpython",
                "source_confidence": "test_source",
                "site_or_file": "https://realpython.github.io/fake-jobs/",
                "use": "Public fake job page used to test scraper parsing.",
            },
            {
                "type": "Courses",
                "source": "Seed Courses",
                "mode": "seed",
                "source_confidence": "fallback_learning",
                "site_or_file": "src/ingestion/seed_sources.py",
                "use": "Offline smoke-test course data.",
            },
            {
                "type": "Courses",
                "source": "YouTube Learning",
                "mode": "youtube",
                "source_confidence": "fallback_learning",
                "site_or_file": "YouTube Data API or local fallback records",
                "use": "Free video learning source. Uses API key when configured.",
            },
            {
                "type": "Courses",
                "source": "Open Course Catalog",
                "mode": "open_catalog",
                "source_confidence": "curated_demo",
                "site_or_file": "freeCodeCamp, Kaggle Learn, Microsoft Learn, Airflow, Databricks, DeepLearning.AI",
                "use": "Learning links that are easy to reproduce locally.",
            },
            {
                "type": "Courses",
                "source": "Microsoft Learn Catalog",
                "mode": "microsoft",
                "source_confidence": "live_verified",
                "site_or_file": "https://learn.microsoft.com/api/catalog/",
                "use": "Live public Microsoft Learn catalog API.",
            },
            {
                "type": "Courses",
                "source": "Vendor Docs Catalog",
                "mode": "vendor_docs",
                "source_confidence": "curated_demo",
                "site_or_file": "Airflow docs, dbt docs, Snowflake docs",
                "use": "Vendor documentation and training resources.",
            },
            {
                "type": "Courses",
                "source": "University Open Catalog",
                "mode": "university_open",
                "source_confidence": "curated_demo",
                "site_or_file": "edX, MIT OpenCourseWare, Coursera browse pages",
                "use": "Open statistics, ML, and visualization resources.",
            },
        ]
    )

def scheduler_summary(runs: pd.DataFrame) -> dict[str, str]:
    latest_timestamp = "No run logged yet"
    next_update = "After the next scheduled interval once scheduler.py is running"
    if not runs.empty and "run_timestamp" in runs:
        parsed = pd.to_datetime(runs["run_timestamp"], errors="coerce", utc=True).dropna()
        if not parsed.empty:
            latest = parsed.max()
            latest_timestamp = latest.strftime("%Y-%m-%d %H:%M UTC")
            next_update = (latest + pd.Timedelta(minutes=settings.schedule_interval_minutes)).strftime("%Y-%m-%d %H:%M UTC")

    return {
        "interval": f"Every {settings.schedule_interval_minutes} minute(s)",
        "run_on_start": "Yes" if settings.scheduler_run_on_start else "No",
        "latest": latest_timestamp,
        "next": next_update,
    }


def render_scheduler_panel(runs: pd.DataFrame) -> None:
    summary = scheduler_summary(runs)
    st.markdown(
        f"""
        <div class="soft-panel">
            <h4>Refresh schedule</h4>
            <p>
                Scheduler cadence: <b>{summary["interval"]}</b> | Run on scheduler start:
                <b>{summary["run_on_start"]}</b><br>
                Last logged pipeline update: <b>{summary["latest"]}</b><br>
                Estimated next update if the scheduler is running: <b>{summary["next"]}</b>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_source_panel(data: dict[str, pd.DataFrame]) -> None:
    observed_rows = []
    for dataset, df in [("Jobs", data["jobs"]), ("Courses", data["courses"])]:
        if not df.empty and "source_name" in df:
            for source_name, count in df.groupby("source_name").size().items():
                observed_rows.append({
                    "dataset": dataset,
                    "active_source": source_name,
                    "source_confidence": confidence_for_source(source_name),
                    "records": int(count),
                })

    st.markdown(f"### Active Data Sources ({data.get('source_view', 'All sources')})")
    if observed_rows:
        st.dataframe(pd.DataFrame(observed_rows), width="stretch", hide_index=True)
    st.markdown(
        """
        **Source sites and files**

        - Adzuna Jobs API: `https://api.adzuna.com/v1/api/jobs/` (requires app id/key)
        - Arbeitnow Job API: `https://www.arbeitnow.com/api/job-board-api`
        - Remotive Jobs API: `https://remotive.com/api/remote-jobs`
        - Sample jobs: `data/sample/curated_data_jobs.csv`
        - Startup and enterprise data jobs: local feeds in `src/ingestion/job_sources.py`
        - Optional legacy/parser sources: YC Jobs and RealPython Fake Jobs
        - YouTube Learning: YouTube Data API if `MARKET_INTEL_YOUTUBE_API_KEY` is configured; local fallback otherwise
        - Course API: `https://learn.microsoft.com/api/catalog/`
        - Open-course catalog: freeCodeCamp, Kaggle Learn, Apache Airflow docs, Databricks training, DeepLearning.AI
        - Vendor docs catalog: Apache Airflow docs, dbt docs, Snowflake docs
        - University/open catalog: edX, MIT OpenCourseWare, Coursera browse pages
        """
    )


def render_overview(data: dict[str, pd.DataFrame]) -> None:
    gaps = data["gaps"]
    jobs = data["jobs"]
    courses = data["courses"]
    trends = data["trends"]
    quality = data["quality"]

    top_skill = gaps.sort_values("opportunity_index", ascending=False).iloc[0]["skill"] if not gaps.empty else "N/A"
    latest_run = trends["run_id"].dropna().iloc[-1] if not trends.empty and "run_id" in trends else "N/A"
    warnings = len(quality[quality["status"].isin(["warning", "fail"])]) if not quality.empty and "status" in quality else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Jobs", f"{len(jobs):,}")
    col2.metric("Courses", f"{len(courses):,}")
    col3.metric("Skills", f"{gaps['skill'].nunique():,}" if "skill" in gaps else "0")
    col4.metric("Top Skill", top_skill)
    col5.metric("Quality Alerts", warnings)

    st.markdown(
        f"""
        <div class="insight-strip">
            Latest run: <b>{latest_run}</b>. Skills are ranked by opportunity score, with demand,
            course supply, target roles, and run history shown below.
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_scheduler_panel(data["runs"])
    render_source_panel(data)

    st.markdown('<div class="section-label">Skill Ranking</div>', unsafe_allow_html=True)
    opportunity_chart = gaps[["skill", "opportunity_index"]].head(12).set_index("skill") if not gaps.empty else pd.DataFrame()
    st.bar_chart(opportunity_chart)

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Demand vs Learning Supply</div>', unsafe_allow_html=True)
    demand_chart = gaps[["skill", "job_demand", "course_supply"]].head(12).set_index("skill") if not gaps.empty else pd.DataFrame()
    st.bar_chart(demand_chart)

    st.markdown("### Skills Worth Checking")
    columns = [
        "skill",
        "category",
        "opportunity_index",
        "opportunity_label",
        "job_demand",
        "course_supply",
        "target_job_roles",
        "onet_evidence_status",
        "onet_workplace_examples",
        "onet_soc_codes",
        "onet_wage_median_annual",
        "onet_growth_outlook",
        "bls_growth_percent",
    ]
    st.dataframe(gaps[columns].head(15), width="stretch", hide_index=True)


def render_trends(data: dict[str, pd.DataFrame]) -> None:
    trends = data["trends"].copy()
    runs = data["runs"].copy()
    if trends.empty:
        st.warning("No trend rows found yet. Run `python pipeline.py` a few times or start the scheduler.")
        return

    trends["run_timestamp"] = pd.to_datetime(trends["run_timestamp"], errors="coerce")
    skill_options = sorted(trends["skill"].dropna().unique())
    default_skills = [skill for skill in ["Python", "SQL", "Power BI", "AWS", "dbt"] if skill in skill_options]
    selected_skills = st.multiselect("Compare skills", skill_options, default=default_skills or skill_options[:5])

    chart_input = trends[trends["skill"].isin(selected_skills)].copy()
    chart_df = (
        chart_input.groupby(["run_timestamp", "skill"], dropna=False)["job_count"]
        .sum()
        .reset_index()
        .pivot(index="run_timestamp", columns="skill", values="job_count")
        .fillna(0)
    )
    st.line_chart(chart_df)

    date_span_days = 0
    if trends["run_timestamp"].notna().any():
        date_span_days = (trends["run_timestamp"].max() - trends["run_timestamp"].min()).days

    if date_span_days >= 7:
        st.markdown("### Weekly Trend View")
        weekly = chart_input.copy()
        weekly["week"] = weekly["run_timestamp"].dt.to_period("W").dt.start_time
        weekly_chart = (
            weekly.groupby(["week", "skill"], dropna=False)["job_count"]
            .sum()
            .reset_index()
            .pivot(index="week", columns="skill", values="job_count")
            .fillna(0)
        )
        st.line_chart(weekly_chart)
    else:
        st.info(f"Weekly view needs at least 7 days of saved runs. Current span: {date_span_days} day(s).")

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown("### Run History")
    if runs.empty:
        st.caption("No pipeline run log found yet.")
    else:
        st.dataframe(runs.tail(20).sort_values("run_timestamp", ascending=False), width="stretch", hide_index=True)

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown("### Trend Records")
    st.dataframe(
        chart_input[
            ["run_id", "run_timestamp", "source_name", "skill", "job_count", "course_count", "location", "role_category"]
        ].tail(100),
        width="stretch",
        hide_index=True,
    )


def render_explorer(data: dict[str, pd.DataFrame]) -> None:
    gaps = data["gaps"].copy()
    jobs = data["jobs"].copy()
    courses = data["courses"].copy()

    skill_options = sorted(gaps["skill"].dropna().unique()) if "skill" in gaps else []
    if not skill_options:
        st.warning("No skills found for the selected data scope. Try All sources or run the pipeline with more source modes enabled.")
        return
    selected_skill = st.selectbox("Pick a skill to inspect", skill_options)

    selected_gap = gaps[gaps["skill"] == selected_skill]
    if not selected_gap.empty:
        row = selected_gap.iloc[0]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Opportunity", int(row.get("opportunity_index", 0)))
        col2.metric("Job Demand", int(row.get("job_demand", 0)))
        col3.metric("Course Supply", int(row.get("course_supply", 0)))
        col4.metric("Label", row.get("opportunity_label", "N/A"))
        st.markdown(f"**Target roles:** {row.get('target_job_roles', 'Data roles')}")

    pattern = rf"(?:^|\|){re.escape(selected_skill)}(?:\||$)"
    matching_jobs = jobs[jobs["skills"].fillna("").str.contains(pattern, regex=True, case=False)] if "skills" in jobs else pd.DataFrame()
    matching_courses = courses[courses["skills"].fillna("").str.contains(pattern, regex=True, case=False)] if "skills" in courses else pd.DataFrame()

    tab_jobs, tab_courses, tab_scores = st.tabs(["Jobs", "Courses", "Score Inputs"])
    with tab_jobs:
        display_cols = [col for col in ["title", "company", "location", "remote_type", "salary_min", "salary_max", "skills", "url"] if col in matching_jobs]
        st.dataframe(matching_jobs[display_cols], width="stretch", hide_index=True)
    with tab_courses:
        display_cols = [col for col in ["title", "platform", "level", "duration_minutes", "skills", "url"] if col in matching_courses]
        st.dataframe(matching_courses[display_cols], width="stretch", hide_index=True)
    with tab_scores:
        score_cols = [
            "skill",
            "demand_score",
            "growth_score",
            "salary_premium_score",
            "course_supply_score",
            "saturation_score",
            "market_direction",
        ]
        st.dataframe(selected_gap[[col for col in score_cols if col in selected_gap]], width="stretch", hide_index=True)


@st.cache_data(ttl=900, show_spinner=False)
def load_practice_projects(skill: str, limit: int = 8) -> dict[str, object]:
    result = recommend_practice_projects(skill=skill, limit=limit)
    return {
        "items": result.items,
        "topic": result.topic,
        "status": result.status,
        "message": result.message,
        "authenticated": result.authenticated,
        "rate_limit_remaining": result.rate_limit_remaining,
        "fetched_at": result.fetched_at,
    }


def render_learning_path(data: dict[str, pd.DataFrame]) -> None:
    certifications = data["certifications"].copy()
    courses = data["courses"].copy()
    gaps = data["gaps"].copy()

    if certifications.empty:
        st.warning("No certification recommendations found for the selected data scope. Try All sources or run `python pipeline.py` with more sources enabled.")
        return

    st.markdown("### Learning & Certification Path")
    st.markdown(
        """
        Start with a skill, then compare related courses, videos, and certifications.
        This is meant to be a practical next-step page, not a perfect career plan.
        """
    )

    skill_options = sorted(certifications["skill"].dropna().unique())
    payment_options = sorted(certifications["free_or_paid"].dropna().unique())
    selected_skills = st.multiselect("Skills", skill_options, default=skill_options[:6])
    selected_payment = st.multiselect("Free or paid", payment_options, default=payment_options)

    filtered = certifications.copy()
    if selected_skills:
        filtered = filtered[filtered["skill"].isin(selected_skills)]
    if selected_payment:
        filtered = filtered[filtered["free_or_paid"].isin(selected_payment)]

    st.markdown("#### Recommended Certifications")
    cert_cols = [
        "skill",
        "certification_name",
        "provider",
        "level",
        "free_or_paid",
        "estimated_cost_usd",
        "recommendation_score",
        "target_roles",
        "url",
    ]
    st.dataframe(filtered[[col for col in cert_cols if col in filtered]], width="stretch", hide_index=True)

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown("#### Related Learning Resources")
    course_filter = courses.copy()
    if selected_skills and "skills" in course_filter:
        pattern = "|".join(re.escape(skill) for skill in selected_skills)
        course_filter = course_filter[course_filter["skills"].fillna("").str.contains(pattern, case=False, regex=True)]
    course_cols = ["title", "platform", "level", "duration_minutes", "skills", "url"]
    st.dataframe(course_filter[[col for col in course_cols if col in course_filter]].head(50), width="stretch", hide_index=True)


    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown("#### Practice This Skill On GitHub")
    practice_choices = selected_skills or skill_options
    practice_skill = st.selectbox(
        "Practice skill",
        practice_choices,
        help="Find open issues in recently updated repositories tagged with this skill.",
    )
    with st.spinner("Looking for current beginner-friendly issues..."):
        practice = load_practice_projects(practice_skill)
    if practice["status"] != "ok":
        st.warning(str(practice["message"]))
    else:
        practice_items = pd.DataFrame(practice["items"])
        auth_label = "token authenticated" if practice["authenticated"] else "public unauthenticated access"
        remaining = practice["rate_limit_remaining"]
        rate_note = f" | search requests remaining: {remaining}" if remaining is not None else ""
        st.caption(
            f"GitHub topic: {practice['topic']} | {auth_label}{rate_note} | fetched {practice['fetched_at']}"
        )
        if practice_items.empty:
            st.info(str(practice["message"]))
        else:
            practice_cols = [
                "repository",
                "issue_title",
                "practice_label",
                "language",
                "stars",
                "issue_updated_at",
                "issue_url",
            ]
            st.dataframe(
                practice_items[[col for col in practice_cols if col in practice_items]],
                width="stretch",
                hide_index=True,
                column_config={"issue_url": st.column_config.LinkColumn("Open issue")},
            )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown("#### Market Context For Selected Skills")
    if selected_skills and "skill" in gaps:
        gaps = gaps[gaps["skill"].isin(selected_skills)]
    explain_cols = ["skill", "opportunity_index", "opportunity_label", "job_demand", "course_supply", "target_job_roles"]
    st.dataframe(gaps[[col for col in explain_cols if col in gaps]].head(30), width="stretch", hide_index=True)


def render_logs_quality(data: dict[str, pd.DataFrame]) -> None:
    render_scheduler_panel(data["runs"])

    st.markdown("### Pipeline Logs")
    runs = data["runs"]
    if runs.empty:
        st.info("No run log found yet. Future pipeline runs will append to `logs/pipeline_runs.csv`.")
    else:
        st.dataframe(runs.sort_values("run_timestamp", ascending=False), width="stretch", hide_index=True)

    scheduler_log = PROJECT_ROOT / "logs" / "scheduler.log"
    if scheduler_log.exists():
        st.markdown("### Scheduler Log Tail")
        st.code("\n".join(scheduler_log.read_text(encoding="utf-8", errors="ignore").splitlines()[-40:]))

    st.markdown("### Data Quality")
    st.dataframe(data["quality"], width="stretch", hide_index=True)


def render_guide(data: dict[str, pd.DataFrame]) -> None:
    st.markdown("### How To Read SkillSync")
    st.markdown(
        """
        **Data Scope** lets you switch between demo-safe records, live sources, a curated market snapshot, or all sources. The dashboard recalculates current skill rankings for the selected source view.

        **Skill Opportunity Index** is a 0 to 100 score based on demand, growth, salary signal,
        course supply, and saturation. I use it as a shortcut for deciding which skills are worth
        looking at first.

        **Trend Lab** reads the `skill_trend_history` files created by each pipeline run. The weekly
        chart is only useful after the project has been running for several days.

        **Target roles** map each skill to likely job titles.

        **Learning & Certification Path** shows courses, certifications, and live GitHub issues where a selected skill can be practiced.
        """
    )

    st.markdown("### Active Sources In This Run")
    source_rows = []
    for name, df in [("Jobs", data["jobs"]), ("Courses", data["courses"])]:
        if not df.empty and "source_name" in df:
            for source_name, count in df.groupby("source_name").size().items():
                source_rows.append({
                    "dataset": name,
                    "source_name": source_name,
                    "source_confidence": confidence_for_source(source_name),
                    "records": count,
                })
    st.dataframe(pd.DataFrame(source_rows), width="stretch", hide_index=True)

    st.markdown("### Supported Job And Course Sources")
    st.dataframe(source_catalog(), width="stretch", hide_index=True)
    st.markdown(
        """
        **Job posting sources**

        - Adzuna Jobs API: `https://api.adzuna.com/v1/api/jobs/` (requires app id/key)
        - Arbeitnow Job API: `https://www.arbeitnow.com/api/job-board-api`
        - Remotive Jobs API: `https://remotive.com/api/remote-jobs`
        - Sample data-role jobs: `data/sample/curated_data_jobs.csv`
        - Startup and enterprise data jobs: local feeds in `src/ingestion/job_sources.py`
        - Optional legacy/parser sources: YC Jobs and RealPython Fake Jobs

        **Course listing sources**

        - Seed course listings: `src/ingestion/seed_sources.py`
        - YouTube Learning: YouTube Data API when `MARKET_INTEL_YOUTUBE_API_KEY` exists; local fallback if not
        - Open Course Catalog: freeCodeCamp, Kaggle Learn, Microsoft Learn, Apache Airflow docs, Databricks training, DeepLearning.AI
        - Microsoft Learn Catalog API: `https://learn.microsoft.com/api/catalog/`
        - Vendor Docs Catalog: Apache Airflow docs, dbt docs, Snowflake docs
        - University Open Catalog: edX, MIT OpenCourseWare, Coursera browse pages

        Use `MARKET_INTEL_JOB_SOURCE_MODE=all` and `MARKET_INTEL_COURSE_SOURCE_MODE=all` to run all current sources.
        """
    )


def main() -> None:
    inject_styles()
    render_header()

    data = load_data()
    data["gaps"] = ensure_columns(
        data["gaps"],
        {
            "opportunity_index": 0,
            "opportunity_label": "Unknown",
            "target_job_roles": "Data Analyst | Data Engineer | Data Scientist",
        },
    )

    if data["jobs"].empty or data["courses"].empty or data["gaps"].empty:
        st.warning("No processed datasets found. Run `python pipeline.py` first.")
        return

    page = st.sidebar.radio(
        "Navigate",
        ["Overview", "Trend Lab", "Skills Explorer", "Learning & Certification Path", "Logs & Quality", "Guide"],
    )
    filtered = filtered_frames(data)

    if page == "Overview":
        render_overview(filtered)
    elif page == "Trend Lab":
        render_trends(filtered)
    elif page == "Skills Explorer":
        render_explorer(filtered)
    elif page == "Learning & Certification Path":
        render_learning_path(filtered)
    elif page == "Logs & Quality":
        render_logs_quality(filtered)
    else:
        render_guide(filtered)


if __name__ == "__main__":
    main()


