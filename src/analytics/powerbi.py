from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analytics.model import latest_run_id, load_latest_outputs, load_trend_history


POWERBI_TABLES = {
    "fact_jobs": "fact_jobs.csv",
    "fact_courses": "fact_courses.csv",
    "fact_skill_gap": "fact_skill_gap.csv",
    "fact_skill_trend": "fact_skill_trend.csv",
    "fact_certification_recommendations": "fact_certification_recommendations.csv",
    "fact_quality_checks": "fact_quality_checks.csv",
    "dim_skill": "dim_skill.csv",
    "dim_company": "dim_company.csv",
    "dim_platform": "dim_platform.csv",
    "bridge_job_skills": "bridge_job_skills.csv",
    "bridge_course_skills": "bridge_course_skills.csv",
}


def export_powerbi_model(output_dir: Path | str = "powerbi/export") -> dict[str, str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

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
    fact_gap = _with_run_id(gaps, run_id)
    fact_trend = _with_run_id_if_missing(trends, run_id)
    fact_certifications = _with_run_id(certifications, run_id)
    fact_quality = _with_run_id(quality, run_id)
    dim_skill = _build_dim_skill(gaps, jobs, courses)
    dim_company = _build_dim_company(jobs)
    dim_platform = _build_dim_platform(courses)
    bridge_job_skills = _build_skill_bridge(jobs, "job_id", run_id)
    bridge_course_skills = _build_skill_bridge(courses, "course_id", run_id)

    tables = {
        "fact_jobs": fact_jobs,
        "fact_courses": fact_courses,
        "fact_skill_gap": fact_gap,
        "fact_skill_trend": fact_trend,
        "fact_certification_recommendations": fact_certifications,
        "fact_quality_checks": fact_quality,
        "dim_skill": dim_skill,
        "dim_company": dim_company,
        "dim_platform": dim_platform,
        "bridge_job_skills": bridge_job_skills,
        "bridge_course_skills": bridge_course_skills,
    }

    exported: dict[str, str] = {}
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
    df.insert(1, "job_id", _keys(df))
    return df.drop(columns=["skills", "skill_categories", "skill_match_terms"], errors="ignore")


def _build_fact_courses(courses: pd.DataFrame, run_id: str) -> pd.DataFrame:
    if courses.empty:
        return pd.DataFrame()
    df = courses.copy()
    df.insert(0, "run_id", run_id)
    df.insert(1, "course_id", _keys(df))
    return df.drop(columns=["skills", "skill_categories", "skill_match_terms"], errors="ignore")


def _build_dim_skill(gaps: pd.DataFrame, jobs: pd.DataFrame, courses: pd.DataFrame) -> pd.DataFrame:
    rows: dict[str, str] = {}
    if not gaps.empty and {"skill", "category"}.issubset(gaps.columns):
        rows.update({str(row.skill): str(row.category) for row in gaps[["skill", "category"]].itertuples(index=False)})

    for df in [jobs, courses]:
        if df.empty or "skills" not in df:
            continue
        categories = df.get("skill_categories", pd.Series([""] * len(df)))
        for skill_text, category_text in zip(df["skills"].fillna(""), categories.fillna("")):
            skills = [skill for skill in str(skill_text).split("|") if skill]
            category = str(category_text).split("|")[0] if category_text else "Other"
            for skill in skills:
                rows.setdefault(skill, category or "Other")

    return pd.DataFrame(
        [{"skill": skill, "category": category} for skill, category in sorted(rows.items())]
    )


def _build_dim_company(jobs: pd.DataFrame) -> pd.DataFrame:
    if jobs.empty or "company" not in jobs:
        return pd.DataFrame(columns=["company"])
    return jobs[["company"]].dropna().drop_duplicates().sort_values("company")


def _build_dim_platform(courses: pd.DataFrame) -> pd.DataFrame:
    if courses.empty or "platform" not in courses:
        return pd.DataFrame(columns=["platform"])
    return courses[["platform"]].dropna().drop_duplicates().sort_values("platform")


def _build_skill_bridge(df: pd.DataFrame, id_column: str, run_id: str) -> pd.DataFrame:
    if df.empty or "skills" not in df:
        return pd.DataFrame(columns=["run_id", id_column, "skill"])

    rows = []
    keys = _keys(df)
    for record_id, skill_text in zip(keys, df["skills"].fillna("")):
        for skill in str(skill_text).split("|"):
            if skill:
                rows.append({"run_id": run_id, id_column: record_id, "skill": skill})
    return pd.DataFrame(rows)


def _with_run_id(df: pd.DataFrame, run_id: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = df.copy()
    out.insert(0, "run_id", run_id)
    return out


def _with_run_id_if_missing(df: pd.DataFrame, run_id: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = df.copy()
    if "run_id" not in out:
        out.insert(0, "run_id", run_id)
    return out


def _keys(df: pd.DataFrame) -> pd.Series:
    source = df.get("source_name", pd.Series(["unknown"] * len(df))).fillna("unknown").astype(str)
    external = df.get("external_id", pd.Series(range(len(df)))).fillna("").astype(str)
    return source + ":" + external
