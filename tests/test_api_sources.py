from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

from src.analytics.model import filter_courses, filter_jobs, normalize_trend_roles, source_summary
from api.main import certifications, scoped_outputs, skill_detail, source_run_history
from src.etl.transform import build_skill_gap_summary


class SourceSummaryTests(unittest.TestCase):
    def test_empty_skill_gap_summary_keeps_stable_schema(self) -> None:
        summary = build_skill_gap_summary(pd.DataFrame(), pd.DataFrame())

        self.assertTrue(summary.empty)
        self.assertIn("opportunity_index", summary.columns)
        self.assertIn("target_job_roles", summary.columns)

    def test_source_summary_keeps_confidence_labels(self) -> None:
        outputs = {
            "jobs": pd.DataFrame(
                [
                    {"source_name": "arbeitnow", "source_confidence": "live_verified"},
                    {"source_name": "arbeitnow", "source_confidence": "live_verified"},
                ]
            ),
            "courses": pd.DataFrame(
                [{"source_name": "seed_courses", "source_confidence": "fallback_learning"}]
            ),
        }

        rows = source_summary(outputs)

        self.assertEqual(
            rows,
            [
                {
                    "dataset": "jobs",
                    "source_name": "arbeitnow",
                    "source_confidence": "live_verified",
                    "record_count": 2,
                },
                {
                    "dataset": "courses",
                    "source_name": "seed_courses",
                    "source_confidence": "fallback_learning",
                    "record_count": 1,
                },
            ],
        )

    @patch("api.main.build_certification_recommendations")
    @patch("api.main.build_skill_gap_summary")
    @patch("api.main.load_latest_outputs")
    def test_scoped_outputs_filters_live_sources_without_mutating_raw_data(
        self,
        load_outputs,
        build_gaps,
        build_certifications,
    ) -> None:
        jobs = pd.DataFrame(
            [
                {"source_name": "arbeitnow_jobs", "title": "Live role"},
                {"source_name": "curated_data_jobs", "title": "Curated role"},
            ]
        )
        courses = pd.DataFrame(
            [
                {"source_name": "microsoft_learn_catalog", "title": "Live course"},
                {"source_name": "open_course_catalog", "title": "Curated course"},
            ]
        )
        load_outputs.return_value = {
            "jobs": jobs,
            "courses": courses,
            "skill_gaps": pd.DataFrame(),
            "certifications": pd.DataFrame(),
        }
        build_gaps.return_value = pd.DataFrame([{"skill": "SQL"}])
        build_certifications.return_value = pd.DataFrame([{"skill": "SQL"}])

        scoped = scoped_outputs("live")

        self.assertEqual(scoped["jobs"]["source_name"].tolist(), ["arbeitnow_jobs"])
        self.assertEqual(scoped["courses"]["source_name"].tolist(), ["microsoft_learn_catalog"])
        self.assertEqual(jobs["source_name"].tolist(), ["arbeitnow_jobs", "curated_data_jobs"])

    def test_role_family_filters_jobs_and_courses(self) -> None:
        jobs = pd.DataFrame(
            [
                {"title": "Backend Engineer", "role_family": "Software Engineering"},
                {"title": "Oracle DBA", "role_family": "Database"},
            ]
        )
        courses = pd.DataFrame(
            [
                {"title": "React", "role_families": "Software Engineering"},
                {"title": "PostgreSQL Admin", "role_families": "Database|Data & Analytics"},
            ]
        )

        filtered_jobs = filter_jobs(jobs, role_family="Database")
        filtered_courses = filter_courses(courses, role_family="Database")

        self.assertEqual(filtered_jobs["title"].tolist(), ["Oracle DBA"])
        self.assertEqual(filtered_courses["title"].tolist(), ["PostgreSQL Admin"])

    def test_legacy_trend_roles_are_normalized(self) -> None:
        trends = pd.DataFrame([
            {"role_category": "Data Engineering", "role_family": None},
            {"role_category": "Data Science", "role_family": ""},
        ])

        normalized = normalize_trend_roles(trends)

        self.assertEqual(normalized["role_category"].tolist(), ["Data Engineer", "Data Scientist"])
        self.assertEqual(normalized["role_family"].tolist(), ["Data & Analytics", "AI & Machine Learning"])

    @patch("api.main.skill_profile")
    @patch("api.main.scoped_outputs")
    def test_skill_detail_passes_role_family_to_scope(self, scoped, profile) -> None:
        scoped.return_value = {"jobs": pd.DataFrame()}
        profile.return_value = {"skill": "Python"}

        result = skill_detail("Python", source_view="curated", role_family="Software Engineering")

        self.assertEqual(result, {"skill": "Python"})
        scoped.assert_called_once_with("curated", "Software Engineering")

    @patch("api.main.scoped_outputs")
    def test_certifications_accepts_role_family_without_runtime_error(self, scoped) -> None:
        scoped.return_value = {
            "certifications": pd.DataFrame([
                {"skill": "Kubernetes", "certification": "CKA", "recommendation_score": 80}
            ])
        }

        rows = certifications(
            source_view="curated",
            skill=None,
            free_or_paid=None,
            role_family="Cloud & Platform",
            limit=100,
        )

        self.assertEqual(rows[0]["certification"], "CKA")
        scoped.assert_called_once_with("curated", "Cloud & Platform")

    def test_source_run_history_filters_and_sorts_activity(self) -> None:
        with TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"
            log_dir.mkdir()
            pd.DataFrame(
                [
                    {
                        "run_id": "run-2",
                        "source_name": "remotive_jobs",
                        "status": "failed",
                        "completed_at": "2026-07-20T10:02:00+00:00",
                    },
                    {
                        "run_id": "run-1",
                        "source_name": "arbeitnow_jobs",
                        "status": "success",
                        "completed_at": "2026-07-20T10:01:00+00:00",
                    },
                ]
            ).to_csv(log_dir / "source_runs.csv", index=False)

            with patch("api.main.PROJECT_ROOT", Path(temp_dir)):
                rows = source_run_history(limit=10, run_id="run-2")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_name"], "remotive_jobs")
        self.assertEqual(rows[0]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
