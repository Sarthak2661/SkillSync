from __future__ import annotations

import re
from typing import Any

import pandas as pd

from src.etl.io import latest_processed_file, read_all_dataframes, read_latest_dataframe


DATASET_NAMES = {
    "jobs": "job_postings_clean",
    "courses": "course_listings_clean",
    "skill_gaps": "skill_gap_summary",
    "skill_trends": "skill_trend_history",
    "certifications": "certification_recommendations",
    "quality": "quality_summary",
}


def load_latest_outputs() -> dict[str, pd.DataFrame]:
    return {name: read_latest_dataframe(dataset) for name, dataset in DATASET_NAMES.items()}


def load_trend_history() -> pd.DataFrame:
    return read_all_dataframes(DATASET_NAMES["skill_trends"])


def latest_run_id() -> str | None:
    path = latest_processed_file("skill_gap_summary")
    if path is None:
        return None
    stem = path.stem
    prefix = "skill_gap_summary_"
    return stem.removeprefix(prefix) if stem.startswith(prefix) else None


def latest_dataset_paths() -> dict[str, str | None]:
    return {
        dataset: str(path) if (path := latest_processed_file(dataset)) else None
        for dataset in DATASET_NAMES.values()
    }


def build_kpis(outputs: dict[str, pd.DataFrame]) -> dict[str, Any]:
    jobs = outputs["jobs"]
    courses = outputs["courses"]
    gaps = outputs["skill_gaps"]
    quality = outputs["quality"]
    trends = load_trend_history()

    high_opportunity = _filter_eq(gaps, "status", "High opportunity")
    warnings = quality[quality["status"].isin(["warning", "fail"])] if "status" in quality else pd.DataFrame()

    return {
        "run_id": latest_run_id(),
        "job_postings": int(len(jobs)),
        "course_listings": int(len(courses)),
        "unique_skills": int(gaps["skill"].nunique()) if "skill" in gaps else 0,
        "high_opportunity_skills": int(len(high_opportunity)),
        "high_value_skills": int(len(_filter_eq(gaps, "opportunity_label", "High-value"))),
        "trend_snapshot_rows": int(len(trends)),
        "historical_runs_available": int(trends["run_id"].nunique()) if "run_id" in trends else 0,
        "quality_warnings": int(len(warnings)),
        "job_skill_coverage": _coverage(jobs),
        "course_skill_coverage": _coverage(courses),
        "top_opportunity_skill": _top_value(gaps, sort_column="opportunity_index", value_column="skill"),
        "top_gap_skill": _top_value(gaps, sort_column="gap_score", value_column="skill"),
        "top_course_heavy_skill": _top_value(gaps, sort_column="gap_score", value_column="skill", ascending=True),
    }


def filter_jobs(
    jobs: pd.DataFrame,
    skill: str | None = None,
    company: str | None = None,
    remote_type: str | None = None,
    limit: int = 100,
) -> pd.DataFrame:
    df = jobs.copy()
    df = _contains_skill(df, skill)
    df = _contains_text(df, "company", company)
    df = _equals_text(df, "remote_type", remote_type)
    return df.head(limit)


def filter_courses(
    courses: pd.DataFrame,
    skill: str | None = None,
    platform: str | None = None,
    level: str | None = None,
    limit: int = 100,
) -> pd.DataFrame:
    df = courses.copy()
    df = _contains_skill(df, skill)
    df = _contains_text(df, "platform", platform)
    df = _contains_text(df, "level", level)
    return df.head(limit)


def filter_skill_gaps(
    gaps: pd.DataFrame,
    status: str | None = None,
    category: str | None = None,
    min_gap: int | None = None,
    min_opportunity: int | None = None,
    label: str | None = None,
    limit: int = 100,
) -> pd.DataFrame:
    df = gaps.copy()
    df = _contains_text(df, "status", status)
    df = _contains_text(df, "category", category)
    df = _contains_text(df, "opportunity_label", label)
    if min_gap is not None and "gap_score" in df:
        df = df[pd.to_numeric(df["gap_score"], errors="coerce").fillna(0) >= min_gap]
    if min_opportunity is not None and "opportunity_index" in df:
        df = df[pd.to_numeric(df["opportunity_index"], errors="coerce").fillna(0) >= min_opportunity]
    return df.head(limit)


def filter_skill_trends(
    trends: pd.DataFrame,
    skill: str | None = None,
    source_name: str | None = None,
    location: str | None = None,
    role_category: str | None = None,
    limit: int = 1000,
) -> pd.DataFrame:
    df = trends.copy()
    df = _contains_text(df, "skill", skill)
    df = _contains_text(df, "source_name", source_name)
    df = _contains_text(df, "location", location)
    df = _contains_text(df, "role_category", role_category)
    if "run_timestamp" in df:
        df = df.sort_values(["run_timestamp", "skill"])
    return df.head(limit)


def skill_profile(skill: str, outputs: dict[str, pd.DataFrame]) -> dict[str, Any]:
    jobs = filter_jobs(outputs["jobs"], skill=skill, limit=500)
    courses = filter_courses(outputs["courses"], skill=skill, limit=500)
    gap_rows = _contains_text(outputs["skill_gaps"], "skill", skill)
    gap = gap_rows.iloc[0].to_dict() if not gap_rows.empty else {}

    return {
        "skill": skill,
        "gap": clean_record(gap),
        "job_count": int(len(jobs)),
        "course_count": int(len(courses)),
        "sample_jobs": dataframe_to_records(jobs.head(10)),
        "sample_courses": dataframe_to_records(courses.head(10)),
    }


def source_summary(outputs: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dataset_name in ["jobs", "courses"]:
        df = outputs[dataset_name]
        if df.empty or "source_name" not in df:
            continue
        grouped = df.groupby("source_name", dropna=False).size().reset_index(name="record_count")
        grouped.insert(0, "dataset", dataset_name)
        rows.extend(dataframe_to_records(grouped))
    return rows


def quality_summary(quality: pd.DataFrame, status: str | None = None, severity: str | None = None) -> pd.DataFrame:
    df = quality.copy()
    df = _contains_text(df, "status", status)
    df = _contains_text(df, "severity", severity)
    return df


def dataframe_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []
    clean_df = df.where(pd.notna(df), None)
    return [clean_record(record) for record in clean_df.to_dict(orient="records")]


def clean_record(record: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in record.items():
        if pd.isna(value):
            clean[key] = None
        elif hasattr(value, "item"):
            clean[key] = value.item()
        else:
            clean[key] = value
    return clean


def _coverage(df: pd.DataFrame) -> float:
    if df.empty or "skill_count" not in df:
        return 0.0
    covered = (pd.to_numeric(df["skill_count"], errors="coerce").fillna(0) > 0).sum()
    return round(float(covered / len(df)), 4)


def _top_value(df: pd.DataFrame, sort_column: str, value_column: str, ascending: bool = False) -> Any:
    if df.empty or sort_column not in df or value_column not in df:
        return None
    sorted_df = df.sort_values(sort_column, ascending=ascending)
    return sorted_df.iloc[0][value_column] if not sorted_df.empty else None


def _filter_eq(df: pd.DataFrame, column: str, value: str) -> pd.DataFrame:
    if df.empty or column not in df:
        return pd.DataFrame()
    return df[df[column] == value]


def _contains_skill(df: pd.DataFrame, skill: str | None) -> pd.DataFrame:
    if not skill or df.empty or "skills" not in df:
        return df
    pattern = rf"(?:^|\|){re.escape(skill)}(?:\||$)"
    return df[df["skills"].fillna("").str.contains(pattern, case=False, regex=True)]


def _contains_text(df: pd.DataFrame, column: str, value: str | None) -> pd.DataFrame:
    if not value or df.empty or column not in df:
        return df
    return df[df[column].fillna("").astype(str).str.contains(value, case=False, regex=False)]


def _equals_text(df: pd.DataFrame, column: str, value: str | None) -> pd.DataFrame:
    if not value or df.empty or column not in df:
        return df
    return df[df[column].fillna("").astype(str).str.lower() == value.lower()]
