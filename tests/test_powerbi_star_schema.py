import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.analytics.powerbi import export_powerbi_model


class PowerBiStarSchemaTests(unittest.TestCase):
    @patch("src.analytics.powerbi.latest_run_id", return_value="20260719_120000")
    @patch("src.analytics.powerbi.load_trend_history")
    @patch("src.analytics.powerbi.load_latest_outputs")
    def test_star_schema_keys_and_relationships(self, mock_outputs, mock_trends, _mock_run_id):
        mock_outputs.return_value = {
            "jobs": pd.DataFrame([{
                "external_id": "job-1", "source_name": "test_jobs", "source_confidence": "test_source",
                "title": "Data Engineer", "location": "Remote", "skills": "Python|SQL",
                "skill_confidence": "high",
            }]),
            "courses": pd.DataFrame([{
                "external_id": "course-1", "source_name": "test_courses", "source_confidence": "test_source",
                "title": "SQL Fundamentals", "skills": "SQL", "skill_confidence": "high",
            }]),
            "skill_gaps": pd.DataFrame([{
                "skill": "SQL", "category": "Data Engineering", "taxonomy_source": "project_taxonomy",
                "onet_evidence_status": "project_fallback", "opportunity_index": 55,
            }]),
            "certifications": pd.DataFrame([{"skill": "SQL", "certification": "SQL Practice"}]),
            "quality": pd.DataFrame([{"dataset": "jobs", "check_name": "row_count", "status": "passed"}]),
        }
        mock_trends.return_value = pd.DataFrame([{
            "run_id": "20260719_120000", "run_timestamp": "2026-07-19T12:00:00Z",
            "source_name": "test_jobs", "skill": "SQL", "location": "Remote",
            "role_category": "Data Engineer", "job_count": 1, "course_count": 1,
            "salary_min_avg": 90000, "salary_max_avg": 120000,
        }])

        with tempfile.TemporaryDirectory() as folder:
            exported = export_powerbi_model(Path(folder))
            expected = {
                "fact_job_skill_mentions",
                "fact_course_skill_coverage",
                "fact_skill_trend_history",
                "dim_skill",
                "dim_role",
                "dim_location",
                "dim_source",
                "dim_time",
                "mart_skill_opportunity",
                "mart_role_skill_demand",
                "mart_role_readiness_inputs",
            }
            self.assertTrue(expected.issubset(exported))

            tables = {name: pd.read_csv(path) for name, path in exported.items()}
            for dimension, key in [
                ("dim_skill", "skill_key"),
                ("dim_role", "role_key"),
                ("dim_location", "location_key"),
                ("dim_source", "source_key"),
                ("dim_time", "time_key"),
            ]:
                self.assertFalse(tables[dimension][key].isna().any())
                self.assertFalse(tables[dimension][key].duplicated().any())

            facts = [
                ("fact_job_skill_mentions", "skill_key", "dim_skill"),
                ("fact_job_skill_mentions", "role_key", "dim_role"),
                ("fact_job_skill_mentions", "location_key", "dim_location"),
                ("fact_job_skill_mentions", "source_key", "dim_source"),
                ("fact_job_skill_mentions", "time_key", "dim_time"),
                ("fact_course_skill_coverage", "skill_key", "dim_skill"),
                ("fact_skill_trend_history", "skill_key", "dim_skill"),
                ("fact_skill_trend_history", "role_key", "dim_role"),
            ]
            for fact, key, dimension in facts:
                orphaned = set(tables[fact][key].dropna()) - set(tables[dimension][key])
                self.assertEqual(orphaned, set(), f"{fact}.{key} has orphaned keys")


if __name__ == "__main__":
    unittest.main()
