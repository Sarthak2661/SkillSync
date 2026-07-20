from __future__ import annotations

import unittest

import pandas as pd

from src.analytics.weekly_report import build_weekly_reports


class WeeklyReportTests(unittest.TestCase):
    def test_uses_latest_run_in_each_week_and_calculates_movement(self) -> None:
        trends = pd.DataFrame(
            [
                {"run_id": "run-1", "run_timestamp": "2026-07-06T09:00:00Z", "skill": "Python", "job_count": 4, "course_count": 2, "role_family": "AI & Machine Learning"},
                {"run_id": "run-2", "run_timestamp": "2026-07-08T09:00:00Z", "skill": "Python", "job_count": 5, "course_count": 2, "role_family": "AI & Machine Learning"},
                {"run_id": "run-2", "run_timestamp": "2026-07-08T09:00:00Z", "skill": "SQL", "job_count": 7, "course_count": 3, "role_family": "Data & Analytics"},
                {"run_id": "run-3", "run_timestamp": "2026-07-15T09:00:00Z", "skill": "Python", "job_count": 9, "course_count": 3, "role_family": "AI & Machine Learning"},
                {"run_id": "run-3", "run_timestamp": "2026-07-15T09:00:00Z", "skill": "SQL", "job_count": 6, "course_count": 3, "role_family": "Data & Analytics"},
            ]
        )
        runs = pd.DataFrame(
            [
                {"run_id": "run-2", "job_records": 12, "course_records": 5, "unique_skills": 2, "top_opportunity_skill": "SQL"},
                {"run_id": "run-3", "job_records": 15, "course_records": 6, "unique_skills": 2, "top_opportunity_skill": "Python"},
            ]
        )
        gaps = pd.DataFrame([{"skill": "Python", "opportunity_index": 91}, {"skill": "SQL", "opportunity_index": 96}])

        reports = build_weekly_reports(trends, gaps, runs)

        self.assertEqual(len(reports), 2)
        self.assertEqual(reports[0]["run_id"], "run-3")
        self.assertEqual(reports[1]["run_id"], "run-2")
        self.assertEqual(reports[0]["rising_skills"][0], {"skill": "Python", "current": 9, "previous": 5, "change": 4})
        self.assertEqual(reports[0]["declining_skills"][0]["skill"], "SQL")
        self.assertIn("not a representative estimate", reports[0]["methodology_note"])

    def test_returns_empty_list_without_trend_history(self) -> None:
        self.assertEqual(build_weekly_reports(pd.DataFrame(), pd.DataFrame(), pd.DataFrame()), [])


if __name__ == "__main__":
    unittest.main()
