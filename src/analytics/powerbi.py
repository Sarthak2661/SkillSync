from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from src.analytics.model import latest_run_id, load_latest_outputs, load_trend_history
from src.etl.transform import infer_role_category


POWERBI_TABLES = {
    "fact_job_skill_mentions": "fact_job_skill_mentions.csv",
    "fact_course_skill_coverage": "fact_course_skill_coverage.csv",
    "fact_skill_trend_history": "fact_skill_trend_history.csv",
    "dim_skill": "dim_skill.csv",
    "dim_role": "dim_role.csv",
    "dim_location": "dim_location.csv",
    "dim_source": "dim_source.csv",
    "dim_time": "dim_time.csv",
    "mart_skill_opportunity": "mart_skill_opportunity.csv",
    "mart_role_skill_demand": "mart_role_skill_demand.csv",
    "mart_role_readiness_inputs": "mart_role_readiness_inputs.csv",
    "fact_jobs": "fact_jobs.csv",
    "fact_courses": "fact_courses.csv",
    "fact_certification_recommendations": "fact_certification_recommendations.csv",
    "fact_quality_checks": "fact_quality_checks.csv",
}


def export_powerbi_model(output_dir: Path | str = "powerbi/export") -> dict[str, str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    for stale_export in output_path.glob("*.csv"):
        stale_export.unlink()
    outputs = load_latest_outputs()
    run_id = latest_run_id() or "unknown_run"

    jobs = outputs["jobs"].copy()
    courses = outputs["courses"].copy()
    gaps = outputs["skill_gaps"].copy()
    trends = load_trend_history()
    certifications = outputs["certifications"].copy()
    quality = outputs["quality"].copy()

    fact_jobs = _build_fact_jobs(jobs, run_id)
    fact_courses = _build_fact_courses(courses, run_id)
    job_mentions = _build_job_skill_mentions(jobs, run_id)
    course_coverage = _build_course_skill_coverage(courses, run_id)
    trend_history = _build_trend_fact(trends)
    dim_skill = _build_dim_skill(gaps, jobs, courses, trends)
    dim_role = _build_dim_role(jobs, trends)
    dim_location = _build_dim_location(jobs, trends)
    dim_source = _build_dim_source(jobs, courses, trends)
    dim_time = _build_dim_time(trends, run_id)
    skill_opportunity = _with_run_id(gaps, run_id).assign(skill_key=lambda df: df["skill"].map(_hash))
    role_skill_demand = _build_role_skill_demand(trend_history)
    readiness = _build_role_readiness(role_skill_demand, course_coverage)

    tables = {
        "fact_job_skill_mentions": job_mentions,
        "fact_course_skill_coverage": course_coverage,
        "fact_skill_trend_history": trend_history,
        "dim_skill": dim_skill,
        "dim_role": dim_role,
        "dim_location": dim_location,
        "dim_source": dim_source,
        "dim_time": dim_time,
        "mart_skill_opportunity": skill_opportunity,
        "mart_role_skill_demand": role_skill_demand,
        "mart_role_readiness_inputs": readiness,
        "fact_jobs": fact_jobs,
        "fact_courses": fact_courses,
        "fact_certification_recommendations": _with_run_id(certifications, run_id),
        "fact_quality_checks": _with_run_id(quality, run_id),
    }

    exported = {}
    for table_name, df in tables.items():
        path = output_path / POWERBI_TABLES[table_name]
        df.to_csv(path, index=False)
        exported[table_name] = str(path)
    return exported


def _build_fact_jobs(jobs: pd.DataFrame, run_id: str) -> pd.DataFrame:
    if jobs.empty:
        return pd.DataFrame()
    df = jobs.copy()
    df.insert(0, "run_id", run_id)
    df.insert(1, "job_key", _keys(df).map(_hash))
    return df.drop(columns=["skills", "skill_categories", "skill_match_terms"], errors="ignore")


def _build_fact_courses(courses: pd.DataFrame, run_id: str) -> pd.DataFrame:
    if courses.empty:
        return pd.DataFrame()
    df = courses.copy()
    df.insert(0, "run_id", run_id)
    df.insert(1, "course_key", _keys(df).map(_hash))
    return df.drop(columns=["skills", "skill_categories", "skill_match_terms"], errors="ignore")


def _build_job_skill_mentions(jobs: pd.DataFrame, run_id: str) -> pd.DataFrame:
    columns = ["job_skill_mention_key", "skill_key", "role_key", "location_key", "source_key", "time_key",
               "run_id", "job_key", "skill_confidence", "high_confidence_demand", "mention_count"]
    if jobs.empty:
        return pd.DataFrame(columns=columns)
    rows = []
    for key, row in zip(_keys(jobs), jobs.to_dict(orient="records")):
        job_key = _hash(key)
        role = infer_role_category(str(row.get("title") or ""))
        for skill in _split(row.get("skills")):
            rows.append({
                "job_skill_mention_key": _hash(f"{job_key}|{skill}"),
                "skill_key": _hash(skill),
                "role_key": _hash(role),
                "location_key": _hash(str(row.get("location") or "Unknown")),
                "source_key": _hash(str(row.get("source_name") or "unknown")),
                "time_key": _hash(run_id),
                "run_id": run_id,
                "job_key": job_key,
                "skill_confidence": row.get("skill_confidence"),
                "high_confidence_demand": int(row.get("source_confidence") == "live_verified"),
                "mention_count": 1,
            })
    return pd.DataFrame(rows, columns=columns)


def _build_course_skill_coverage(courses: pd.DataFrame, run_id: str) -> pd.DataFrame:
    columns = ["course_skill_coverage_key", "skill_key", "source_key", "time_key", "run_id",
               "course_key", "skill_confidence", "coverage_count"]
    if courses.empty:
        return pd.DataFrame(columns=columns)
    rows = []
    for key, row in zip(_keys(courses), courses.to_dict(orient="records")):
        course_key = _hash(key)
        for skill in _split(row.get("skills")):
            rows.append({
                "course_skill_coverage_key": _hash(f"{course_key}|{skill}"),
                "skill_key": _hash(skill),
                "source_key": _hash(str(row.get("source_name") or "unknown")),
                "time_key": _hash(run_id),
                "run_id": run_id,
                "course_key": course_key,
                "skill_confidence": row.get("skill_confidence"),
                "coverage_count": 1,
            })
    return pd.DataFrame(rows, columns=columns)


def _build_trend_fact(trends: pd.DataFrame) -> pd.DataFrame:
    if trends.empty:
        return pd.DataFrame()
    df = trends.copy()
    df.insert(0, "skill_trend_key", df.apply(lambda row: _hash("|".join(str(row.get(c, "")) for c in
              ["run_id", "source_name", "skill", "location", "role_category"])), axis=1))
    df.insert(1, "skill_key", df["skill"].astype(str).map(_hash))
    df.insert(2, "role_key", df["role_category"].astype(str).map(_hash))
    df.insert(3, "location_key", df["location"].astype(str).map(_hash))
    df.insert(4, "source_key", df["source_name"].astype(str).map(_hash))
    df.insert(5, "time_key", df["run_id"].astype(str).map(_hash))
    return df.drop(columns=["skill", "role_category", "location", "source_name"], errors="ignore")


def _build_dim_skill(gaps: pd.DataFrame, jobs: pd.DataFrame, courses: pd.DataFrame, trends: pd.DataFrame) -> pd.DataFrame:
    rows = {}
    if not gaps.empty:
        for row in gaps.to_dict(orient="records"):
            rows[str(row["skill"])] = {
                "category": row.get("category", "Other"),
                "taxonomy_source": row.get("taxonomy_source", ""),
                "onet_evidence_status": row.get("onet_evidence_status", "project_fallback"),
            }
    for df in (jobs, courses):
        for skill_text in df.get("skills", pd.Series(dtype=str)).fillna(""):
            for skill in _split(skill_text):
                rows.setdefault(skill, {"category": "Other", "taxonomy_source": "", "onet_evidence_status": "project_fallback"})
    if not trends.empty and "skill" in trends:
        for skill in trends["skill"].dropna().astype(str).unique():
            rows.setdefault(skill, {"category": "Other", "taxonomy_source": "", "onet_evidence_status": "project_fallback"})
    return pd.DataFrame([{"skill_key": _hash(skill), "skill": skill, **values} for skill, values in sorted(rows.items())])


def _build_dim_role(jobs: pd.DataFrame, trends: pd.DataFrame) -> pd.DataFrame:
    roles = {infer_role_category(str(title)) for title in jobs.get("title", pd.Series(dtype=str)).fillna("")}
    roles.update(trends.get("role_category", pd.Series(dtype=str)).dropna().astype(str))
    return pd.DataFrame([{"role_key": _hash(role), "role_name": role} for role in sorted(roles)])


def _build_dim_location(jobs: pd.DataFrame, trends: pd.DataFrame) -> pd.DataFrame:
    values = set(jobs.get("location", pd.Series(dtype=str)).fillna("Unknown").astype(str))
    values.update(trends.get("location", pd.Series(dtype=str)).dropna().astype(str))
    return pd.DataFrame([{"location_key": _hash(value), "location": value} for value in sorted(values)])


def _build_dim_source(jobs: pd.DataFrame, courses: pd.DataFrame, trends: pd.DataFrame) -> pd.DataFrame:
    confidence = {}
    for df in (jobs, courses):
        for row in df.to_dict(orient="records"):
            confidence[str(row.get("source_name") or "unknown")] = str(row.get("source_confidence") or "test_source")
    for source in trends.get("source_name", pd.Series(dtype=str)).dropna().astype(str):
        confidence.setdefault(source, "test_source")
    return pd.DataFrame([{"source_key": _hash(source), "source_name": source, "source_confidence": value}
                         for source, value in sorted(confidence.items())])


def _build_dim_time(trends: pd.DataFrame, run_id: str) -> pd.DataFrame:
    rows = {}
    if not trends.empty:
        for row in trends[["run_id", "run_timestamp"]].drop_duplicates().to_dict(orient="records"):
            rows[str(row["run_id"])] = row.get("run_timestamp")
    rows.setdefault(run_id, pd.to_datetime(run_id, format="%Y%m%d_%H%M%S", errors="coerce", utc=True))
    output = []
    for current_run, timestamp in sorted(rows.items()):
        value = pd.to_datetime(timestamp, errors="coerce", utc=True)
        output.append({"time_key": _hash(current_run), "run_id": current_run, "run_timestamp": value,
                       "year": value.year if not pd.isna(value) else None,
                       "month": value.month if not pd.isna(value) else None,
                       "week": value.isocalendar().week if not pd.isna(value) else None,
                       "day": value.day if not pd.isna(value) else None})
    return pd.DataFrame(output)


def _build_role_skill_demand(trends: pd.DataFrame) -> pd.DataFrame:
    if trends.empty:
        return pd.DataFrame(columns=["role_key", "skill_key", "time_key", "job_demand", "salary_min_avg", "salary_max_avg"])
    return trends.groupby(["role_key", "skill_key", "time_key"], as_index=False).agg(
        job_demand=("job_count", "sum"), salary_min_avg=("salary_min_avg", "mean"), salary_max_avg=("salary_max_avg", "mean"))


def _build_role_readiness(demand: pd.DataFrame, courses: pd.DataFrame) -> pd.DataFrame:
    if demand.empty:
        return pd.DataFrame(columns=["role_key", "skill_key", "job_demand", "course_supply", "readiness_gap"])
    demand_total = demand.groupby(["role_key", "skill_key"], as_index=False)["job_demand"].sum()
    supply = courses.groupby("skill_key", as_index=False)["coverage_count"].sum().rename(columns={"coverage_count": "course_supply"})
    out = demand_total.merge(supply, on="skill_key", how="left")
    out["course_supply"] = out["course_supply"].fillna(0).astype(int)
    out["readiness_gap"] = out["job_demand"] - out["course_supply"]
    return out


def _with_run_id(df: pd.DataFrame, run_id: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = df.copy()
    out.insert(0, "run_id", run_id)
    return out


def _keys(df: pd.DataFrame) -> pd.Series:
    source = df.get("source_name", pd.Series(["unknown"] * len(df))).fillna("unknown").astype(str)
    external = df.get("external_id", pd.Series(range(len(df)))).fillna("").astype(str)
    return source + ":" + external


def _split(value: object) -> list[str]:
    if value is None or pd.isna(value):
        return []
    return [item for item in str(value).split("|") if item]


def _hash(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()
