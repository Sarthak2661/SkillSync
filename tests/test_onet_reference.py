import json
import unittest
from pathlib import Path

from src.analytics.onet_reference import onet_growth_score, onet_profile_for_skill


class OnetReferenceTests(unittest.TestCase):
    def test_exact_software_skill_has_verified_evidence(self):
        profile = onet_profile_for_skill("Airflow")
        self.assertEqual(profile.evidence_status, "software_skill_verified")
        self.assertIn("Apache Airflow", profile.onet_workplace_examples)

    def test_conceptual_skill_is_disclosed_as_mapping(self):
        profile = onet_profile_for_skill("Data Quality")
        self.assertEqual(profile.evidence_status, "occupation_mapping_only")
        self.assertEqual(profile.onet_workplace_examples, ())

    def test_growth_scores_use_numeric_projection_rates(self):
        self.assertGreater(onet_growth_score("Python"), onet_growth_score("SQL"))

    def test_compact_snapshot_has_source_and_license(self):
        evidence = json.loads(Path("data/reference/onet_software_skill_evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["database_version"], "30.3")
        self.assertEqual(evidence["license"], "CC BY 4.0")
        self.assertTrue(evidence["records"])


if __name__ == "__main__":
    unittest.main()
