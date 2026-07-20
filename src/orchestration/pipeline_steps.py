from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from src.analytics.certifications import build_certification_recommendations
from src.analytics.powerbi import export_powerbi_model
from src.config.settings import settings
from src.etl.io import run_timestamp, save_dataframe, save_raw_records
from src.etl.transform import (
    build_skill_gap_summary,
    build_skill_trend_history,
    normalize_course_listings,
    normalize_job_postings,
)
from src.ingestion.base import RawRecord, SourceFetchStatus, fetch_with_status
from src.quality.checks import summarize_quality
from src.warehouse.postgres import load_pipeline_outputs


def ingest_sources(job_source: Any, course_source: Any, run_id: str | None = None) -> dict[str, str]:
    run_id = run_id or run_timestamp()
    job_records, job_statuses = _fetch_records(job_source, (requests.RequestException,))
    course_records, course_statuses = _fetch_records(course_source, (requests.RequestException, ValueError))
    source_status_path = _append_source_run_log(run_id, job_statuses + course_statuses)

    raw_jobs_path = save_raw_records(job_records, "job_postings_raw", run_id)
    raw_courses_path = save_raw_records(course_records, "course_listings_raw", run_id)

    return {
        "run_id": run_id,
        "raw_jobs": str(raw_jobs_path),
        "raw_courses": str(raw_courses_path),
        "job_records": str(len(job_records)),
        "course_records": str(len(course_records)),
        "source_run_log": str(source_status_path),
    }



def _fetch_records(
    source: Any,
    handled_errors: tuple[type[Exception], ...],
) -> tuple[list[RawRecord], list[SourceFetchStatus]]:
    records, top_status = fetch_with_status(source, handled_errors)
    child_statuses = getattr(source, "fetch_statuses", None)
    return records, list(child_statuses) if child_statuses else [top_status]


def _append_source_run_log(run_id: str, statuses: list[SourceFetchStatus]) -> Path:
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / "source_runs.csv"

    rows = []
    for status in statuses:
        row = asdict(status)
        row["started_at"] = status.started_at.isoformat()
        row["completed_at"] = status.completed_at.isoformat()
        row["run_id"] = run_id
        rows.append(row)

    if rows:
        pd.DataFrame(rows).to_csv(path, mode="a", header=not path.exists(), index=False)
    return path

def transform_raw_records(raw_jobs_path: str, raw_courses_path: str, run_id: str) -> dict[str, str]:
    job_records = read_raw_records(raw_jobs_path)
    course_records = read_raw_records(raw_courses_path)

    jobs_df = normalize_job_postings(job_records)
    courses_df = normalize_course_listings(course_records)
    skill_gap_df = build_skill_gap_summary(jobs_df, courses_df)
    skill_trend_df = build_skill_trend_history(jobs_df, courses_df, run_id)
    certification_df = build_certification_recommendations(skill_gap_df)

    jobs_path = save_dataframe(jobs_df, "job_postings_clean", run_id)
    courses_path = save_dataframe(courses_df, "course_listings_clean", run_id)
    skill_gap_path = save_dataframe(skill_gap_df, "skill_gap_summary", run_id)
    skill_trend_path = save_dataframe(skill_trend_df, "skill_trend_history", run_id)
    certification_path = save_dataframe(certification_df, "certification_recommendations", run_id)

    return {
        "run_id": run_id,
        "clean_jobs": str(jobs_path),
        "clean_courses": str(courses_path),
        "skill_gap_summary": str(skill_gap_path),
        "skill_trend_history": str(skill_trend_path),
        "certification_recommendations": str(certification_path),
    }


def run_quality_checks(clean_jobs_path: str, clean_courses_path: str, skill_gap_path: str, run_id: str) -> dict[str, str]:
    jobs_df = pd.read_csv(clean_jobs_path)
    courses_df = pd.read_csv(clean_courses_path)
    skill_gap_df = pd.read_csv(skill_gap_path)
    quality_df = summarize_quality(jobs_df, courses_df, skill_gap_df)
    quality_path = save_dataframe(quality_df, "quality_summary", run_id)
    return {"run_id": run_id, "quality_summary": str(quality_path)}


def export_powerbi_files() -> dict[str, str]:
    return export_powerbi_model()


def load_postgres_if_enabled(
    clean_jobs_path: str,
    clean_courses_path: str,
    skill_gap_path: str,
    skill_trend_path: str,
    certification_path: str,
    quality_path: str,
    run_id: str,
) -> str:
    if not settings.load_to_postgres:
        return "skipped"

    load_pipeline_outputs(
        run_id=run_id,
        jobs_df=pd.read_csv(clean_jobs_path),
        courses_df=pd.read_csv(clean_courses_path),
        skill_gap_df=pd.read_csv(skill_gap_path),
        skill_trend_df=pd.read_csv(skill_trend_path),
        certification_df=pd.read_csv(certification_path),
        quality_df=pd.read_csv(quality_path),
    )
    return "loaded"


def write_run_log_from_paths(
    run_id: str,
    clean_jobs_path: str,
    clean_courses_path: str,
    skill_gap_path: str,
    skill_trend_path: str,
    warehouse_status: str,
) -> None:
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / "pipeline_runs.csv"

    jobs_df = pd.read_csv(clean_jobs_path)
    courses_df = pd.read_csv(clean_courses_path)
    skill_gap_df = pd.read_csv(skill_gap_path)
    skill_trend_df = pd.read_csv(skill_trend_path)

    row = {
        "run_id": run_id,
        "run_timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
        "job_records": len(jobs_df),
        "course_records": len(courses_df),
        "unique_skills": skill_gap_df["skill"].nunique() if "skill" in skill_gap_df else 0,
        "trend_rows": len(skill_trend_df),
        "top_opportunity_skill": skill_gap_df.iloc[0]["skill"] if not skill_gap_df.empty else None,
        "postgres": warehouse_status,
    }
    pd.DataFrame([row]).to_csv(path, mode="a", header=not path.exists(), index=False)


def read_raw_records(path: str | Path) -> list[RawRecord]:
    records: list[RawRecord] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            collected_at = row.get("collected_at")
            records.append(
                RawRecord(
                    source_name=row["source_name"],
                    source_type=row["source_type"],
                    source_url=row["source_url"],
                    collected_at=datetime.fromisoformat(collected_at),
                    payload=row["payload"],
                )
            )
    return records
