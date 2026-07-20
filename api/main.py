from __future__ import annotations

from dataclasses import asdict
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

import pandas as pd

from src.analytics.model import (
    build_kpis,
    dataframe_to_records,
    filter_courses,
    filter_jobs,
    filter_skill_gaps,
    filter_skill_trends,
    latest_dataset_paths,
    latest_run_id,
    load_trend_history,
    load_latest_outputs,
    quality_summary,
    skill_profile,
    source_summary,
)
from src.analytics.github_practice import recommend_practice_projects
from src.analytics.certifications import build_certification_recommendations
from src.analytics.source_confidence import SOURCE_VIEW_OPTIONS, filter_by_sources
from src.analytics.weekly_report import build_weekly_reports
from src.domain.technology import ROLE_FAMILIES
from src.config.settings import settings
from src.etl.io import latest_processed_file
from src.etl.transform import build_skill_gap_summary


app = FastAPI(
    title="SkillSync API",
    description="API for market demand, learning paths, practice issues, trends, and quality checks.",
    version="0.4.0",
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORS_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"
allowed_origins = [
    origin.strip()
    for origin in os.getenv("MARKET_INTEL_CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

SOURCE_VIEW_NAMES = {
    "demo": "Demo-safe data",
    "live": "Live sources only",
    "curated": "Curated market snapshot",
    "all": "All sources",
}


def scoped_outputs(source_view: str = "all", role_family: str | None = None) -> dict[str, pd.DataFrame]:
    outputs = load_latest_outputs()
    view_name = SOURCE_VIEW_NAMES.get(source_view, "All sources")
    config = SOURCE_VIEW_OPTIONS[view_name]
    if view_name == "All sources" and not role_family:
        return outputs

    scoped = outputs.copy()
    jobs = filter_by_sources(outputs["jobs"], config["jobs"])
    courses = filter_by_sources(outputs["courses"], config["courses"])
    scoped["jobs"] = filter_jobs(jobs, role_family=role_family, limit=max(len(jobs), 1))
    scoped["courses"] = filter_courses(courses, role_family=role_family, limit=max(len(courses), 1))
    history = load_trend_history()
    if config["jobs"] is not None and not history.empty and "source_name" in history:
        history = history[history["source_name"].isin(config["jobs"])].copy()
    scoped["trend_history"] = filter_skill_trends(
        history,
        role_family=role_family,
        limit=max(len(history), 1),
    )
    scoped["skill_gaps"] = build_skill_gap_summary(scoped["jobs"], scoped["courses"])
    scoped["certifications"] = (
        build_certification_recommendations(scoped["skill_gaps"])
        if not scoped["skill_gaps"].empty
        else outputs["certifications"].iloc[0:0].copy()
    )
    return scoped


@app.get("/")
def root() -> dict[str, object]:
    return {
        "message": "SkillSync API is running",
        "run_pipeline": "python pipeline.py",
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/runs/latest",
            "/runs",
            "/source-runs",
            "/scheduler",
            "/kpis",
            "/skill-gaps",
            "/skill-trends",
            "/weekly-reports",
            "/skills/{skill}",
            "/jobs",
            "/courses",
            "/quality",
            "/certifications",
            "/practice-projects",
            "/sources",
            "/role-families",
            "/datasets",
        ],
    }


@app.get("/health")
def health() -> dict[str, object]:
    paths = latest_dataset_paths()
    missing = [name for name, path in paths.items() if path is None]
    return {
        "status": "ok" if not missing else "missing_data",
        "latest_run_id": latest_run_id(),
        "missing_datasets": missing,
    }


@app.get("/runs/latest")
def latest_run() -> dict[str, object]:
    outputs = load_latest_outputs()
    return {
        "run_id": latest_run_id(),
        "datasets": latest_dataset_paths(),
        "record_counts": {name: int(len(df)) for name, df in outputs.items()},
    }

@app.get("/runs")
def run_history(limit: int = Query(50, ge=1, le=500)) -> list[dict[str, Any]]:
    path = PROJECT_ROOT / "logs" / "pipeline_runs.csv"
    if not path.exists():
        return []
    runs = pd.read_csv(path)
    if "run_timestamp" in runs:
        runs = runs.sort_values("run_timestamp", ascending=False)
    return dataframe_to_records(runs.head(limit))



@app.get("/source-runs")
def source_run_history(
    limit: int = Query(200, ge=1, le=2000),
    run_id: str | None = Query(None, description="Filter source activity by pipeline run ID."),
) -> list[dict[str, Any]]:
    path = PROJECT_ROOT / "logs" / "source_runs.csv"
    if not path.exists():
        return []
    source_runs = pd.read_csv(path)
    if run_id and "run_id" in source_runs:
        source_runs = source_runs[source_runs["run_id"].astype(str) == run_id]
    if "completed_at" in source_runs:
        source_runs = source_runs.sort_values("completed_at", ascending=False)
    return dataframe_to_records(source_runs.head(limit))

@app.get("/scheduler")
def scheduler_status() -> dict[str, Any]:
    runs = run_history(limit=1)
    latest = runs[0].get("run_timestamp") if runs else None
    next_run = None
    if latest:
        parsed = pd.to_datetime(latest, errors="coerce", utc=True)
        if pd.notna(parsed):
            next_run = (parsed + pd.Timedelta(minutes=settings.schedule_interval_minutes)).isoformat()
    return {
        "interval_minutes": settings.schedule_interval_minutes,
        "run_on_start": settings.scheduler_run_on_start,
        "latest_run_timestamp": latest,
        "estimated_next_run": next_run,
    }


@app.get("/weekly-reports")
def weekly_reports(
    source_view: str = Query("all", pattern="^(demo|live|curated|all)$"),
    role_family: str | None = Query(None, description="Filter by technology role family."),
    limit: int = Query(12, ge=1, le=52),
) -> list[dict[str, Any]]:
    outputs = scoped_outputs(source_view, role_family)
    runs_path = PROJECT_ROOT / "logs" / "pipeline_runs.csv"
    runs = pd.read_csv(runs_path) if runs_path.exists() else pd.DataFrame()
    trends = outputs.get("trend_history")
    if trends is None:
        trends = load_trend_history()
    return build_weekly_reports(
        trends,
        outputs["skill_gaps"],
        runs,
        limit=limit,
    )


@app.get("/kpis")
def kpis(
    source_view: str = Query("all", pattern="^(demo|live|curated|all)$"),
    role_family: str | None = Query(None, description="Filter by technology role family."),
) -> dict[str, Any]:
    return build_kpis(scoped_outputs(source_view, role_family))


@app.get("/skill-gaps")
def skill_gaps(
    source_view: str = Query("all", pattern="^(demo|live|curated|all)$"),
    role_family: str | None = Query(None, description="Filter by technology role family."),
    status: str | None = Query(None, description="Filter by status, such as High opportunity."),
    category: str | None = Query(None, description="Filter by skill category."),
    min_gap: int | None = Query(None, description="Minimum gap score."),
    min_opportunity: int | None = Query(None, ge=0, le=100, description="Minimum Skill Opportunity Index."),
    label: str | None = Query(None, description="Filter by opportunity label, such as High-value."),
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    outputs = scoped_outputs(source_view, role_family)
    df = filter_skill_gaps(
        outputs["skill_gaps"],
        status=status,
        category=category,
        min_gap=min_gap,
        min_opportunity=min_opportunity,
        label=label,
        limit=limit,
    )
    return dataframe_to_records(df)


@app.get("/skill-trends")
def skill_trends(
    source_view: str = Query("all", pattern="^(demo|live|curated|all)$"),
    skill: str | None = Query(None, description="Filter by skill, such as Python or SQL."),
    source_name: str | None = Query(None, description="Filter by source name."),
    location: str | None = Query(None, description="Filter by location text."),
    role_category: str | None = Query(None, description="Filter by role category."),
    limit: int = Query(1000, ge=1, le=10000),
    role_family: str | None = Query(None, description="Filter by technology role family."),
) -> list[dict[str, Any]]:
    history = load_trend_history()
    view_name = SOURCE_VIEW_NAMES.get(source_view, "All sources")
    source_names = SOURCE_VIEW_OPTIONS[view_name]["jobs"]
    if source_names is not None and not history.empty and "source_name" in history:
        history = history[history["source_name"].isin(source_names)]
    df = filter_skill_trends(
        history,
        skill=skill,
        source_name=source_name,
        location=location,
        role_category=role_category,
        limit=limit,
        role_family=role_family,
    )
    return dataframe_to_records(df)


@app.get("/skills/{skill}")
def skill_detail(
    skill: str,
    source_view: str = Query("all", pattern="^(demo|live|curated|all)$"),
    role_family: str | None = Query(None, description="Filter by technology role family."),
) -> dict[str, Any]:
    return skill_profile(skill, scoped_outputs(source_view, role_family))


@app.get("/jobs")
def jobs(
    source_view: str = Query("all", pattern="^(demo|live|curated|all)$"),
    skill: str | None = Query(None, description="Filter jobs containing a skill."),
    company: str | None = Query(None, description="Filter by company text."),
    remote_type: str | None = Query(None, description="Filter by Remote, Hybrid, or On-site."),
    role_family: str | None = Query(None, description="Filter by technology role family."),
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    outputs = scoped_outputs(source_view, role_family)
    df = filter_jobs(outputs["jobs"], skill=skill, company=company, remote_type=remote_type, limit=limit)
    return dataframe_to_records(df)


@app.get("/courses")
def courses(
    source_view: str = Query("all", pattern="^(demo|live|curated|all)$"),
    skill: str | None = Query(None, description="Filter courses containing a skill."),
    platform: str | None = Query(None, description="Filter by learning platform."),
    level: str | None = Query(None, description="Filter by level text."),
    limit: int = Query(100, ge=1, le=1000),
    role_family: str | None = Query(None, description="Filter by technology role family."),
) -> list[dict[str, Any]]:
    outputs = scoped_outputs(source_view, role_family)
    df = filter_courses(outputs["courses"], skill=skill, platform=platform, level=level, limit=limit)
    return dataframe_to_records(df)


@app.get("/certifications")
def certifications(
    source_view: str = Query("all", pattern="^(demo|live|curated|all)$"),
    skill: str | None = Query(None, description="Filter by skill."),
    free_or_paid: str | None = Query(None, description="Filter by Free or Paid."),
    role_family: str | None = Query(None, description="Filter by technology role family."),
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    outputs = scoped_outputs(source_view, role_family)
    df = outputs["certifications"].copy()
    if skill and "skill" in df:
        df = df[df["skill"].fillna("").astype(str).str.contains(skill, case=False, regex=False)]
    if free_or_paid and "free_or_paid" in df:
        df = df[df["free_or_paid"].fillna("").astype(str).str.lower() == free_or_paid.lower()]
    if "recommendation_score" in df:
        df = df.sort_values("recommendation_score", ascending=False)
    return dataframe_to_records(df.head(limit))


@app.get("/practice-projects")
def practice_projects(
    skill: str = Query(..., min_length=1, description="Skill topic, such as dbt or Airflow."),
    limit: int = Query(8, ge=1, le=20),
) -> dict[str, Any]:
    """Return recently updated, beginner-friendly issues from skill-tagged GitHub repositories."""
    return asdict(recommend_practice_projects(skill=skill, limit=limit))


@app.get("/quality")
def quality(
    status: str | None = Query(None, description="Filter by pass, warning, or fail."),
    severity: str | None = Query(None, description="Filter by low, medium, or high."),
) -> list[dict[str, Any]]:
    outputs = load_latest_outputs()
    df = quality_summary(outputs["quality"], status=status, severity=severity)
    return dataframe_to_records(df)


@app.get("/sources")
def sources(
    source_view: str = Query("all", pattern="^(demo|live|curated|all)$"),
    role_family: str | None = Query(None, description="Filter by technology role family."),
) -> list[dict[str, Any]]:
    return source_summary(scoped_outputs(source_view, role_family))


@app.get("/datasets")
def datasets() -> dict[str, str | None]:
    names = [
        "job_postings_clean",
        "course_listings_clean",
        "skill_gap_summary",
        "skill_trend_history",
        "certification_recommendations",
        "quality_summary",
    ]
    return {name: str(path) if (path := latest_processed_file(name)) else None for name in names}


@app.get("/role-families")
def role_families() -> dict[str, object]:
    outputs = load_latest_outputs()
    jobs = outputs["jobs"]
    counts = jobs["role_family"].value_counts().to_dict() if "role_family" in jobs else {}
    return {"role_families": list(ROLE_FAMILIES), "job_counts": counts}
