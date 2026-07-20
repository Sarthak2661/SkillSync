from datetime import datetime, timezone
import unittest

import pandas as pd

from src.analytics.source_confidence import SOURCE_VIEW_OPTIONS, confidence_for_source, filter_by_sources, filter_trends
from src.etl.transform import build_skill_gap_summary, normalize_course_listings, normalize_job_postings
from src.ingestion.base import RawRecord
from src.quality.checks import _duplicate_urls, _trusted_url_domains, summarize_quality

class SourceConfidenceTests(unittest.TestCase):
    def test_source_confidence_mapping(self):
        self.assertEqual(confidence_for_source("microsoft_learn_catalog"), "live_verified")
        self.assertEqual(confidence_for_source("freecodecamp_curriculum"), "live_verified")
        self.assertEqual(confidence_for_source("github_learning_paths"), "live_broad")
        self.assertEqual(confidence_for_source("adzuna_jobs"), "live_verified")
        self.assertEqual(confidence_for_source("arbeitnow_jobs"), "live_verified")
        self.assertEqual(confidence_for_source("remotive_jobs"), "live_verified")
        self.assertEqual(confidence_for_source("hackernews_who_is_hiring"), "live_broad")
        self.assertEqual(confidence_for_source("curated_data_jobs"), "curated_demo")
        self.assertEqual(confidence_for_source("youtube_learning"), "fallback_learning")
        self.assertEqual(confidence_for_source("seed_job_postings"), "test_source")

    def test_normalized_records_include_source_confidence(self):
        collected_at = datetime(2026, 7, 18, tzinfo=timezone.utc)
        jobs = normalize_job_postings(
            [
                RawRecord(
                    source_name="curated_data_jobs",
                    source_type="job_posting",
                    source_url="https://example.com/jobs/1",
                    collected_at=collected_at,
                    payload={
                        "external_id": "job-1",
                        "title": "Data Engineer",
                        "company": "Example",
                        "location": "Remote",
                        "remote_type": "Remote",
                        "description": "Python SQL Airflow",
                        "posted_at": "2026-07-01",
                        "url": "https://example.com/jobs/1",
                    },
                )
            ]
        )
        courses = normalize_course_listings(
            [
                RawRecord(
                    source_name="microsoft_learn_catalog",
                    source_type="course_listing",
                    source_url="https://learn.microsoft.com/training/modules/example",
                    collected_at=collected_at,
                    payload={
                        "external_id": "course-1",
                        "title": "SQL analytics",
                        "platform": "Microsoft Learn",
                        "description": "SQL and Power BI",
                        "url": "https://learn.microsoft.com/training/modules/example",
                    },
                )
            ]
        )

        self.assertEqual(jobs.loc[0, "source_confidence"], "curated_demo")
        self.assertEqual(courses.loc[0, "source_confidence"], "live_verified")

class QualityCheckTests(unittest.TestCase):
    def test_quality_checks_include_source_confidence(self):
        jobs = pd.DataFrame(
            [
                {
                    "source_name": "curated_data_jobs",
                    "source_confidence": "curated_demo",
                    "external_id": "j1",
                    "title": "Data Engineer",
                    "company": "Example",
                    "url": "https://example.com/jobs/1",
                    "skills": "Python|SQL",
                    "skill_count": 2,
                    "salary_min": 100000,
                    "salary_max": 140000,
                    "posted_at": "2026-07-01",
                }
            ]
        )
        courses = pd.DataFrame(
            [
                {
                    "source_name": "microsoft_learn_catalog",
                    "source_confidence": "not_a_label",
                    "external_id": "c1",
                    "title": "SQL Analytics",
                    "platform": "Microsoft Learn",
                    "url": "https://learn.microsoft.com/training/modules/example",
                    "skills": "SQL",
                    "skill_count": 1,
                    "last_modified": "2026-01-01",
                }
            ]
        )
        gaps = build_skill_gap_summary(jobs, courses)

        quality = summarize_quality(jobs, courses, gaps)
        confidence_rows = quality[quality["check_name"] == "source_confidence_labels"]

        self.assertEqual(len(confidence_rows), 2)
        self.assertEqual(confidence_rows[confidence_rows["dataset"] == "jobs"].iloc[0]["status"], "pass")
        self.assertEqual(confidence_rows[confidence_rows["dataset"] == "courses"].iloc[0]["status"], "warning")

    def test_duplicate_course_urls_are_detected_across_sources(self):
        courses = pd.DataFrame({"url": ["https://example.com/course", "https://example.com/course/"]})
        result = _duplicate_urls(courses, "courses")

        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["failed_count"], 1)

    def test_trusted_domain_check_accepts_official_subdomains(self):
        courses = pd.DataFrame({"url": ["https://docs.oracle.com/en/database/"]})

        result = _trusted_url_domains(courses, "courses", {"oracle.com"})

        self.assertEqual(result["status"], "pass")

class SourceModeFilterTests(unittest.TestCase):
    def test_source_mode_filters_jobs_courses_and_trends(self):
        jobs = pd.DataFrame(
            [
                {"source_name": "curated_data_jobs", "skills": "Python"},
                {"source_name": "remotive_jobs", "skills": "SQL"},
                {"source_name": "seed_job_postings", "skills": "Excel"},
            ]
        )
        courses = pd.DataFrame(
            [
                {"source_name": "open_course_catalog", "skills": "Python"},
                {"source_name": "microsoft_learn_catalog", "skills": "SQL"},
                {"source_name": "seed_course_listings", "skills": "Excel"},
            ]
        )
        trends = pd.DataFrame(
            [
                {"source_name": "curated_data_jobs", "skill": "Python", "job_count": 1},
                {"source_name": "remotive_jobs", "skill": "SQL", "job_count": 1},
                {"source_name": "seed_job_postings", "skill": "Excel", "job_count": 1},
            ]
        )

        curated = SOURCE_VIEW_OPTIONS["Curated market snapshot"]
        live = SOURCE_VIEW_OPTIONS["Live sources only"]

        curated_jobs = filter_by_sources(jobs, curated["jobs"])
        curated_courses = filter_by_sources(courses, curated["courses"])
        live_trends = filter_trends(trends, live["jobs"], {"SQL", "Python"})

        self.assertEqual(curated_jobs["source_name"].tolist(), ["curated_data_jobs"])
        self.assertEqual(curated_courses["source_name"].tolist(), ["open_course_catalog"])
        self.assertEqual(live_trends["source_name"].tolist(), ["remotive_jobs"])
        self.assertNotIn("youtube_learning", live["courses"])


if __name__ == "__main__":
    unittest.main()
