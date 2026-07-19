import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.analytics.powerbi import export_powerbi_model


class PowerBiStarSchemaTests(unittest.TestCase):
    def test_star_schema_keys_and_relationships(self):
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
