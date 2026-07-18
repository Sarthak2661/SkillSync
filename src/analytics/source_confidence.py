from __future__ import annotations

import pandas as pd

SOURCE_CONFIDENCE_LABELS = (
    "live_verified",
    "live_broad",
    "curated_demo",
    "fallback_learning",
    "test_source",
)

SOURCE_CONFIDENCE_BY_SOURCE = {
    "microsoft_learn_catalog": "live_verified",
    "adzuna_jobs": "live_verified",
    "arbeitnow_jobs": "live_verified",
    "remotive_jobs": "live_verified",
    "ycombinator_jobs": "live_broad",
    "curated_data_jobs": "curated_demo",
    "startup_data_jobs": "curated_demo",
    "enterprise_analytics_jobs": "curated_demo",
    "open_course_catalog": "curated_demo",
    "vendor_docs_catalog": "curated_demo",
    "university_open_catalog": "curated_demo",
    "youtube_learning": "fallback_learning",
    "seed_course_listings": "fallback_learning",
    "seed_job_postings": "test_source",
    "realpython_fake_jobs": "test_source",
}

SOURCE_VIEW_OPTIONS = {
    "Demo-safe data": {
        "jobs": {"seed_job_postings", "curated_data_jobs", "startup_data_jobs", "enterprise_analytics_jobs"},
        "courses": {"seed_course_listings", "open_course_catalog", "vendor_docs_catalog", "university_open_catalog"},
        "description": "Repeatable local/sample records that are safe for demos and screenshots.",
    },
    "Live sources only": {
        "jobs": {"adzuna_jobs", "arbeitnow_jobs", "remotive_jobs"},
        "courses": {"microsoft_learn_catalog", "youtube_learning"},
        "description": "Records collected from official/public job APIs and learning APIs in the latest run.",
    },
    "Curated market snapshot": {
        "jobs": {"curated_data_jobs", "startup_data_jobs", "enterprise_analytics_jobs"},
        "courses": {"open_course_catalog", "vendor_docs_catalog", "university_open_catalog"},
        "description": "Cleaner data-role job descriptions plus maintained learning catalogs for portfolio screenshots.",
    },
    "All sources": {
        "jobs": None,
        "courses": None,
        "description": "Every job and course source included in the latest pipeline output.",
    },
}


def confidence_for_source(source_name: object) -> str:
    return SOURCE_CONFIDENCE_BY_SOURCE.get(str(source_name or "").strip(), "test_source")


def add_source_confidence(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        if "source_confidence" not in out.columns:
            out["source_confidence"] = pd.Series(dtype="object")
        return out
    if "source_name" not in out.columns:
        out["source_confidence"] = "test_source"
        return out
    out["source_confidence"] = out["source_name"].map(confidence_for_source)
    return out

def filter_by_sources(df: pd.DataFrame, source_names: set[str] | None) -> pd.DataFrame:
    if source_names is None or df.empty or "source_name" not in df:
        return df.copy()
    return df[df["source_name"].isin(source_names)].copy()


def filter_trends(trends: pd.DataFrame, job_source_names: set[str] | None, selected_skills: set[str]) -> pd.DataFrame:
    if trends.empty:
        return trends.copy()
    out = trends.copy()
    if job_source_names is not None and "source_name" in out:
        out = out[out["source_name"].isin(job_source_names)]
    if selected_skills and "skill" in out:
        out = out[out["skill"].isin(selected_skills)]
    return out
