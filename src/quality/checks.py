from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse

import pandas as pd


TRUSTED_JOB_DOMAINS = {"example.com", "realpython.github.io", "www.ycombinator.com", "ycombinator.com"}
TRUSTED_COURSE_DOMAINS = {
    "airflow.apache.org",
    "coursera.org",
    "databricks.com",
    "deeplearning.ai",
    "docs.getdbt.com",
    "docs.snowflake.com",
    "edx.org",
    "example.com",
    "freecodecamp.org",
    "kaggle.com",
    "learn.microsoft.com",
    "ocw.mit.edu",
    "youtube.com",
    "www.youtube.com",
}


def summarize_quality(
    jobs_df: pd.DataFrame,
    courses_df: pd.DataFrame,
    skill_gap_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    checks = [
        _missing_required(jobs_df, "jobs", ["external_id", "title", "company", "url"]),
        _missing_required(courses_df, "courses", ["external_id", "title", "platform", "url"]),
        _duplicates(jobs_df, "jobs", ["source_name", "external_id"]),
        _duplicates(courses_df, "courses", ["source_name", "external_id"]),
        _salary_anomalies(jobs_df),
        _empty_skills(jobs_df, "jobs"),
        _empty_skills(courses_df, "courses"),
        _trusted_url_domains(jobs_df, "jobs", TRUSTED_JOB_DOMAINS),
        _trusted_url_domains(courses_df, "courses", TRUSTED_COURSE_DOMAINS),
        _posting_freshness(jobs_df),
        _course_freshness(courses_df),
        _sample_size_check(jobs_df, courses_df),
        _skill_gap_support_check(skill_gap_df),
    ]
    return pd.DataFrame(checks)


def _missing_required(df: pd.DataFrame, dataset: str, columns: list[str]) -> dict[str, object]:
    if df.empty:
        return _result(dataset, "required_fields_present", "warning", "high", 0, 0, "Dataset is empty.")

    missing_count = int(df[columns].isna().any(axis=1).sum())
    status = "pass" if missing_count == 0 else "fail"
    return _result(
        dataset,
        "required_fields_present",
        status,
        "high",
        len(df),
        missing_count,
        f"{missing_count} records have missing required fields.",
    )


def _duplicates(df: pd.DataFrame, dataset: str, columns: list[str]) -> dict[str, object]:
    if df.empty:
        return _result(dataset, "duplicate_records", "warning", "medium", 0, 0, "Dataset is empty.")

    duplicate_count = int(df.duplicated(subset=columns).sum())
    status = "pass" if duplicate_count == 0 else "fail"
    return _result(
        dataset,
        "duplicate_records",
        status,
        "medium",
        len(df),
        duplicate_count,
        f"{duplicate_count} duplicate records found.",
    )


def _salary_anomalies(df: pd.DataFrame) -> dict[str, object]:
    if df.empty or not {"salary_min", "salary_max"}.issubset(df.columns):
        return _result("jobs", "salary_range_valid", "warning", "medium", 0, 0, "No salary fields available.")

    salaries = df[["salary_min", "salary_max"]].apply(pd.to_numeric, errors="coerce")
    salary_rows = salaries.dropna(how="all")
    invalid = salary_rows[
        (salary_rows["salary_min"] < 20000)
        | (salary_rows["salary_max"] > 500000)
        | (salary_rows["salary_min"] > salary_rows["salary_max"])
    ]
    status = "pass" if invalid.empty else "fail"
    severity = "high" if len(invalid) else "medium"
    return _result(
        "jobs",
        "salary_range_valid",
        status,
        severity,
        len(salary_rows),
        len(invalid),
        f"{len(invalid)} salary anomalies found across {len(salary_rows)} records with salary data.",
    )


def _empty_skills(df: pd.DataFrame, dataset: str) -> dict[str, object]:
    if df.empty or "skill_count" not in df:
        return _result(dataset, "skills_extracted", "warning", "medium", 0, 0, "No skill fields available.")

    empty_count = int((df["skill_count"].fillna(0) == 0).sum())
    coverage = 1 - (empty_count / len(df)) if len(df) else 0
    status = "pass" if coverage >= 0.75 else "warning"
    return _result(
        dataset,
        "skills_extracted",
        status,
        "medium",
        len(df),
        empty_count,
        f"{empty_count} records have no extracted skills; coverage is {coverage:.1%}.",
    )


def _trusted_url_domains(df: pd.DataFrame, dataset: str, trusted_domains: set[str]) -> dict[str, object]:
    if df.empty or "url" not in df:
        return _result(dataset, "trusted_source_domains", "warning", "medium", 0, 0, "No URL fields available.")

    invalid_count = 0
    for url in df["url"].fillna(""):
        domain = urlparse(str(url)).netloc.lower()
        domain = domain[4:] if domain.startswith("www.") else domain
        if domain not in trusted_domains:
            invalid_count += 1

    status = "pass" if invalid_count == 0 else "warning"
    return _result(
        dataset,
        "trusted_source_domains",
        status,
        "medium",
        len(df),
        invalid_count,
        f"{invalid_count} records use URLs outside trusted domains: {', '.join(sorted(trusted_domains))}.",
    )


def _posting_freshness(df: pd.DataFrame) -> dict[str, object]:
    if df.empty or "posted_at" not in df:
        return _result("jobs", "posting_date_freshness", "warning", "low", 0, 0, "No posting dates available.")

    posted_at = pd.to_datetime(df["posted_at"], errors="coerce", utc=True)
    dated = posted_at.dropna()
    if dated.empty:
        return _result("jobs", "posting_date_freshness", "warning", "low", len(df), len(df), "No parseable posting dates.")

    now = pd.Timestamp.now(tz=timezone.utc)
    stale_count = int(((now - dated).dt.days > 365).sum())
    future_count = int((dated > now).sum())
    issue_count = stale_count + future_count
    status = "pass" if issue_count == 0 else "warning"
    return _result(
        "jobs",
        "posting_date_freshness",
        status,
        "low",
        len(dated),
        issue_count,
        f"{stale_count} postings are older than 365 days and {future_count} are future-dated.",
    )


def _course_freshness(df: pd.DataFrame) -> dict[str, object]:
    if df.empty or "last_modified" not in df:
        return _result("courses", "course_freshness", "warning", "low", 0, 0, "No course freshness field available.")

    last_modified = pd.to_datetime(df["last_modified"], errors="coerce", utc=True)
    dated = last_modified.dropna()
    if dated.empty:
        return _result("courses", "course_freshness", "warning", "low", len(df), len(df), "No parseable course dates.")

    now = pd.Timestamp.now(tz=timezone.utc)
    stale_count = int(((now - dated).dt.days > 730).sum())
    status = "pass" if stale_count == 0 else "warning"
    return _result(
        "courses",
        "course_freshness",
        status,
        "low",
        len(dated),
        stale_count,
        f"{stale_count} courses have not been modified in more than 730 days.",
    )


def _sample_size_check(jobs_df: pd.DataFrame, courses_df: pd.DataFrame) -> dict[str, object]:
    job_count = len(jobs_df)
    course_count = len(courses_df)
    ready = job_count >= 30 and course_count >= 30
    status = "pass" if ready else "warning"
    return _result(
        "pipeline",
        "sample_size_ready",
        status,
        "high",
        job_count + course_count,
        0 if ready else 1,
        f"Trend views work best with at least 30 jobs and 30 courses; current sample is {job_count} jobs and {course_count} courses.",
    )


def _skill_gap_support_check(skill_gap_df: pd.DataFrame | None) -> dict[str, object]:
    if skill_gap_df is None or skill_gap_df.empty:
        return _result("skill_gaps", "skill_gap_support", "warning", "high", 0, 0, "No skill gap summary available.")

    demand = pd.to_numeric(skill_gap_df.get("job_demand"), errors="coerce").fillna(0)
    supply = pd.to_numeric(skill_gap_df.get("course_supply"), errors="coerce").fillna(0)
    supported = int(((demand + supply) >= 3).sum())
    unsupported = int(len(skill_gap_df) - supported)
    status = "pass" if supported >= 3 else "warning"
    return _result(
        "skill_gaps",
        "skill_gap_support",
        status,
        "high",
        len(skill_gap_df),
        unsupported,
        f"{supported} skill-gap rows have at least 3 supporting records across demand and supply.",
    )


def _result(
    dataset: str,
    check_name: str,
    status: str,
    severity: str,
    records_checked: int,
    failed_count: int,
    message: str,
) -> dict[str, object]:
    return {
        "dataset": dataset,
        "check_name": check_name,
        "status": status,
        "severity": severity,
        "records_checked": records_checked,
        "failed_count": failed_count,
        "message": message,
    }
