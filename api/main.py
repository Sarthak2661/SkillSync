from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import FastAPI, Query

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
from src.etl.io import latest_processed_file


app = FastAPI(
    title="SkillSync API",
    description="API for market demand, learning paths, practice issues, trends, and quality checks.",
    version="0.3.0",
)


@app.get("/")
def root() -> dict[str, object]:
    return {
        "message": "SkillSync API is running",
        "run_pipeline": "python pipeline.py",
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/runs/latest",
            "/kpis",
            "/skill-gaps",
            "/skill-trends",
            "/skills/{skill}",
            "/jobs",
            "/courses",
            "/quality",
            "/certifications",
            "/practice-projects",
            "/sources",
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


@app.get("/kpis")
def kpis() -> dict[str, Any]:
    return build_kpis(load_latest_outputs())


@app.get("/skill-gaps")
def skill_gaps(
    status: str | None = Query(None, description="Filter by status, such as High opportunity."),
    category: str | None = Query(None, description="Filter by skill category."),
    min_gap: int | None = Query(None, description="Minimum gap score."),
    min_opportunity: int | None = Query(None, ge=0, le=100, description="Minimum Skill Opportunity Index."),
    label: str | None = Query(None, description="Filter by opportunity label, such as High-value."),
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    outputs = load_latest_outputs()
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
    skill: str | None = Query(None, description="Filter by skill, such as Python or SQL."),
    source_name: str | None = Query(None, description="Filter by source name."),
    location: str | None = Query(None, description="Filter by location text."),
    role_category: str | None = Query(None, description="Filter by role category."),
    limit: int = Query(1000, ge=1, le=10000),
) -> list[dict[str, Any]]:
    df = filter_skill_trends(
        load_trend_history(),
        skill=skill,
        source_name=source_name,
        location=location,
        role_category=role_category,
        limit=limit,
    )
    return dataframe_to_records(df)


@app.get("/skills/{skill}")
def skill_detail(skill: str) -> dict[str, Any]:
    return skill_profile(skill, load_latest_outputs())


@app.get("/jobs")
def jobs(
    skill: str | None = Query(None, description="Filter jobs containing a skill."),
    company: str | None = Query(None, description="Filter by company text."),
    remote_type: str | None = Query(None, description="Filter by Remote, Hybrid, or On-site."),
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    outputs = load_latest_outputs()
    df = filter_jobs(outputs["jobs"], skill=skill, company=company, remote_type=remote_type, limit=limit)
    return dataframe_to_records(df)


@app.get("/courses")
def courses(
    skill: str | None = Query(None, description="Filter courses containing a skill."),
    platform: str | None = Query(None, description="Filter by learning platform."),
    level: str | None = Query(None, description="Filter by level text."),
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    outputs = load_latest_outputs()
    df = filter_courses(outputs["courses"], skill=skill, platform=platform, level=level, limit=limit)
    return dataframe_to_records(df)


@app.get("/certifications")
def certifications(
    skill: str | None = Query(None, description="Filter by skill."),
    free_or_paid: str | None = Query(None, description="Filter by Free or Paid."),
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    outputs = load_latest_outputs()
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
def sources() -> list[dict[str, Any]]:
    return source_summary(load_latest_outputs())


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
