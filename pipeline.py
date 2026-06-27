from __future__ import annotations

from src.etl.io import run_timestamp, save_dataframe, save_raw_records
from src.analytics.certifications import build_certification_recommendations
from src.etl.transform import (
    build_skill_gap_summary,
    build_skill_trend_history,
    normalize_course_listings,
    normalize_job_postings,
)
from src.config.settings import settings
from src.ingestion.course_sources import (
    CompositeCourseSource,
    MicrosoftLearnCourseSource,
    OpenCourseCatalogSource,
    UniversityOpenCourseSource,
    VendorDocsCourseSource,
    YouTubeLearningSource,
)
from src.ingestion.curated_job_source import CuratedDataJobsSource
from src.ingestion.job_sources import (
    CompositeJobSource,
    EnterpriseAnalyticsJobsSource,
    RealPythonFakeJobsSource,
    StartupDataJobsSource,
    YCombinatorJobsSource,
)
from src.ingestion.seed_sources import SeedCourseListingSource, SeedJobPostingSource
from src.quality.checks import summarize_quality
from src.warehouse.postgres import load_pipeline_outputs


def run_pipeline() -> dict[str, str]:
    run_id = run_timestamp()

    job_records = get_job_source().fetch()
    course_records = get_course_source().fetch()

    raw_jobs_path = save_raw_records(job_records, "job_postings_raw", run_id)
    raw_courses_path = save_raw_records(course_records, "course_listings_raw", run_id)

    jobs_df = normalize_job_postings(job_records)
    courses_df = normalize_course_listings(course_records)
    skill_gap_df = build_skill_gap_summary(jobs_df, courses_df)
    skill_trend_df = build_skill_trend_history(jobs_df, courses_df, run_id)
    certification_df = build_certification_recommendations(skill_gap_df)
    quality_df = summarize_quality(jobs_df, courses_df, skill_gap_df)

    jobs_path = save_dataframe(jobs_df, "job_postings_clean", run_id)
    courses_path = save_dataframe(courses_df, "course_listings_clean", run_id)
    skill_gap_path = save_dataframe(skill_gap_df, "skill_gap_summary", run_id)
    skill_trend_path = save_dataframe(skill_trend_df, "skill_trend_history", run_id)
    certification_path = save_dataframe(certification_df, "certification_recommendations", run_id)
    quality_path = save_dataframe(quality_df, "quality_summary", run_id)

    warehouse_status = "skipped"
    if settings.load_to_postgres:
        load_pipeline_outputs(
            run_id=run_id,
            jobs_df=jobs_df,
            courses_df=courses_df,
            skill_gap_df=skill_gap_df,
            skill_trend_df=skill_trend_df,
            certification_df=certification_df,
            quality_df=quality_df,
        )
        warehouse_status = "loaded"

    outputs = {
        "run_id": run_id,
        "raw_jobs": str(raw_jobs_path),
        "raw_courses": str(raw_courses_path),
        "clean_jobs": str(jobs_path),
        "clean_courses": str(courses_path),
        "skill_gap_summary": str(skill_gap_path),
        "skill_trend_history": str(skill_trend_path),
        "certification_recommendations": str(certification_path),
        "quality_summary": str(quality_path),
        "postgres": warehouse_status,
    }
    write_run_log(run_id, jobs_df, courses_df, skill_gap_df, skill_trend_df, warehouse_status)
    return outputs


def get_job_source():
    mode = settings.job_source_mode.strip().lower()
    if mode == "seed":
        return SeedJobPostingSource()
    if mode in {"curated", "curated_data", "portfolio"}:
        return CuratedDataJobsSource()
    if mode in {"startup", "startup_data"}:
        return StartupDataJobsSource()
    if mode in {"enterprise", "enterprise_analytics"}:
        return EnterpriseAnalyticsJobsSource()
    if mode in {"realpython", "realpython_fake_jobs", "scrape"}:
        return RealPythonFakeJobsSource()
    if mode in {"yc", "ycombinator", "y_combinator"}:
        return YCombinatorJobsSource()
    if mode in {"all", "all_demo", "portfolio_all", "five_sources"}:
        return CompositeJobSource(
            [
                CuratedDataJobsSource(),
                StartupDataJobsSource(),
                EnterpriseAnalyticsJobsSource(),
                YCombinatorJobsSource(),
                RealPythonFakeJobsSource(),
            ]
        )
    raise ValueError(
        f"Unsupported job source mode '{settings.job_source_mode}'. "
        "Use 'seed', 'curated', 'startup', 'enterprise', 'yc', 'realpython', or 'all'."
    )


def get_course_source():
    mode = settings.course_source_mode.strip().lower()
    if mode == "seed":
        return SeedCourseListingSource()
    if mode in {"open", "open_catalog", "curated_open"}:
        return OpenCourseCatalogSource()
    if mode in {"vendor", "vendor_docs"}:
        return VendorDocsCourseSource()
    if mode in {"university", "university_open"}:
        return UniversityOpenCourseSource()
    if mode in {"youtube", "youtube_learning"}:
        return YouTubeLearningSource()
    if mode in {"hybrid", "portfolio", "multi"}:
        return CompositeCourseSource([SeedCourseListingSource(), OpenCourseCatalogSource()])
    if mode in {"all", "all_demo", "portfolio_all", "five_sources"}:
        return CompositeCourseSource(
            [
                YouTubeLearningSource(),
                OpenCourseCatalogSource(),
                VendorDocsCourseSource(),
                UniversityOpenCourseSource(),
                MicrosoftLearnCourseSource(),
            ]
        )
    if mode in {"microsoft_open", "microsoft_hybrid"}:
        return CompositeCourseSource([MicrosoftLearnCourseSource(), OpenCourseCatalogSource()])
    if mode in {"microsoft", "microsoft_learn", "learn"}:
        return MicrosoftLearnCourseSource()
    raise ValueError(
        f"Unsupported course source mode '{settings.course_source_mode}'. "
        "Use 'seed', 'open_catalog', 'vendor_docs', 'university_open', 'youtube', 'hybrid', 'microsoft', 'microsoft_open', or 'all'."
    )


def write_run_log(run_id, jobs_df, courses_df, skill_gap_df, skill_trend_df, warehouse_status: str) -> None:
    from pathlib import Path

    import pandas as pd

    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / "pipeline_runs.csv"
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
    df = pd.DataFrame([row])
    df.to_csv(path, mode="a", header=not path.exists(), index=False)


def main() -> None:
    outputs = run_pipeline()
    print("Pipeline run complete.")
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
