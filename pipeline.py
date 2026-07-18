from __future__ import annotations

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
    AdzunaJobsSource,
    ArbeitnowJobsSource,
    CompositeJobSource,
    EnterpriseAnalyticsJobsSource,
    RealPythonFakeJobsSource,
    RemotiveJobsSource,
    StartupDataJobsSource,
    YCombinatorJobsSource,
)
from src.ingestion.seed_sources import SeedCourseListingSource, SeedJobPostingSource
from src.orchestration.pipeline_steps import (
    ingest_sources,
    load_postgres_if_enabled,
    run_quality_checks,
    transform_raw_records,
    write_run_log_from_paths,
)


def run_pipeline() -> dict[str, str]:
    ingested = ingest_sources(get_job_source(), get_course_source())
    run_id = ingested["run_id"]
    transformed = transform_raw_records(ingested["raw_jobs"], ingested["raw_courses"], run_id)
    quality = run_quality_checks(
        transformed["clean_jobs"],
        transformed["clean_courses"],
        transformed["skill_gap_summary"],
        run_id,
    )
    warehouse_status = load_postgres_if_enabled(
        clean_jobs_path=transformed["clean_jobs"],
        clean_courses_path=transformed["clean_courses"],
        skill_gap_path=transformed["skill_gap_summary"],
        skill_trend_path=transformed["skill_trend_history"],
        certification_path=transformed["certification_recommendations"],
        quality_path=quality["quality_summary"],
        run_id=run_id,
    )

    outputs = {
        "run_id": run_id,
        "raw_jobs": ingested["raw_jobs"],
        "raw_courses": ingested["raw_courses"],
        "clean_jobs": transformed["clean_jobs"],
        "clean_courses": transformed["clean_courses"],
        "skill_gap_summary": transformed["skill_gap_summary"],
        "skill_trend_history": transformed["skill_trend_history"],
        "certification_recommendations": transformed["certification_recommendations"],
        "quality_summary": quality["quality_summary"],
        "postgres": warehouse_status,
    }
    write_run_log_from_paths(
        run_id=run_id,
        clean_jobs_path=transformed["clean_jobs"],
        clean_courses_path=transformed["clean_courses"],
        skill_gap_path=transformed["skill_gap_summary"],
        skill_trend_path=transformed["skill_trend_history"],
        warehouse_status=warehouse_status,
    )
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
    if mode in {"yc", "ycombinator", "y_combinator", "legacy_yc"}:
        return YCombinatorJobsSource()
    if mode in {"adzuna", "adzuna_jobs"}:
        return AdzunaJobsSource()
    if mode in {"arbeitnow", "arbeitnow_jobs"}:
        return ArbeitnowJobsSource()
    if mode in {"remotive", "remotive_jobs"}:
        return RemotiveJobsSource()
    if mode in {"job_apis", "official_apis", "api_jobs"}:
        return CompositeJobSource([AdzunaJobsSource(), ArbeitnowJobsSource(), RemotiveJobsSource()])
    if mode in {"all", "all_demo", "portfolio_all", "five_sources"}:
        return CompositeJobSource(
            [
                CuratedDataJobsSource(),
                StartupDataJobsSource(),
                EnterpriseAnalyticsJobsSource(),
                AdzunaJobsSource(),
                ArbeitnowJobsSource(),
                RemotiveJobsSource(),
            ]
        )
    raise ValueError(
        f"Unsupported job source mode '{settings.job_source_mode}'. "
        "Use 'seed', 'curated', 'startup', 'enterprise', 'adzuna', 'arbeitnow', 'remotive', 'job_apis', 'yc', 'realpython', or 'all'."
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


def main() -> None:
    outputs = run_pipeline()
    print("Pipeline run complete.")
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()