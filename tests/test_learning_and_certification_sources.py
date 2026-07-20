from __future__ import annotations

from unittest import TestCase
from unittest.mock import Mock, patch

import pandas as pd

from src.analytics.certifications import build_certification_recommendations
from src.config.settings import settings
from src.ingestion.certification_sources import (
    CredentialEngineCertificationSource,
    load_certification_catalog,
)
from src.ingestion.course_sources import UNIVERSITY_OPEN_CATALOG
from src.ingestion.learning_sources import FreeCodeCampCurriculumSource, GitHubLearningPathSource


class LearningSourceTests(TestCase):
    def test_freecodecamp_curriculum_uses_official_github_index(self):
        response = Mock()
        response.json.return_value = [
            {
                "name": "data-analysis-with-python.yml",
                "type": "file",
                "path": "curriculum/challenges/english/certifications/data-analysis-with-python.yml",
                "html_url": "https://github.com/freeCodeCamp/freeCodeCamp/blob/main/data-analysis-with-python.yml",
            }
        ]
        session = Mock()
        session.get.return_value = response

        records = FreeCodeCampCurriculumSource(session=session).fetch()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source_name, "freecodecamp_curriculum")
        self.assertEqual(records[0].payload["platform"], "freeCodeCamp Curriculum")
        self.assertIn("data-analysis-with-python", records[0].payload["url"])
        session.get.assert_called_once()

    def test_github_learning_paths_only_accepts_safe_curated_repository_metadata(self):
        response = Mock()
        response.json.return_value = {
            "items": [
                {
                    "id": 42,
                    "full_name": "example/awesome-data-engineering",
                    "name": "awesome-data-engineering",
                    "html_url": "https://github.com/example/awesome-data-engineering",
                    "archived": False,
                    "pushed_at": "2026-07-01T00:00:00Z",
                    "description": "External repository description should not be copied.",
                }
            ]
        }
        session = Mock()
        session.get.return_value = response

        with patch.object(settings, "github_learning_path_limit", 1):
            records = GitHubLearningPathSource(session=session).fetch()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source_name, "github_learning_paths")
        self.assertEqual(records[0].payload["title"], "Data Pipelines learning path: example/awesome-data-engineering")
        self.assertNotIn("should not be copied", records[0].payload["description"])

    def test_excluded_commercial_catalogs_are_not_in_curated_university_rows(self):
        urls = " ".join(row["url"] for row in UNIVERSITY_OPEN_CATALOG).lower()
        self.assertNotIn("coursera", urls)
        self.assertNotIn("udemy", urls)
        self.assertNotIn("khanacademy", urls)


class CertificationSourceTests(TestCase):
    def test_curated_mode_contains_cloud_and_freecodecamp_credentials(self):
        rows = load_certification_catalog("curated")
        providers = {row["provider"] for row in rows}

        expected = {"AWS", "Microsoft", "Google Cloud", "freeCodeCamp", "HashiCorp", "Red Hat", "Cisco"}
        self.assertTrue(expected.issubset(providers))
        self.assertIn("Linux Foundation and CNCF", providers)
        self.assertTrue(all("source_name" in row and "source_confidence" in row for row in rows))

    def test_credential_engine_normalizes_json_ld_results(self):
        response = Mock()
        response.json.return_value = {
            "Results": [
                {
                    "Resource": {
                        "ceterms:name": {"en": "Applied SQL Analytics Certificate"},
                        "ceterms:description": {"en": "SQL and relational database analysis."},
                        "ceterms:ownedBy": {"ceterms:name": {"en": "Example College"}},
                        "ceterms:subjectWebpage": "https://example.edu/sql-certificate",
                    }
                }
            ]
        }
        session = Mock()
        session.post.return_value = response

        with patch.object(settings, "credential_engine_api_key", "test-key"):
            rows = CredentialEngineCertificationSource(session=session).fetch()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["skill"], "SQL")
        self.assertEqual(rows[0]["provider"], "Example College")
        self.assertEqual(rows[0]["source_confidence"], "live_verified")
        self.assertEqual(session.post.call_args.kwargs["headers"]["Authorization"], "Bearer test-key")

    def test_recommendation_output_keeps_catalog_provenance(self):
        gaps = pd.DataFrame(
            [{"skill": "AWS", "opportunity_index": 75, "opportunity_label": "High-value", "job_demand": 10}]
        )

        output = build_certification_recommendations(gaps)
        aws = output[output["certification_name"] == "AWS Certified Data Engineer - Associate"].iloc[0]

        self.assertEqual(aws["source_name"], "curated_cloud_certifications")
        self.assertEqual(aws["source_confidence"], "curated_demo")
        self.assertEqual(aws["role_families"], "Cloud & Platform")
        self.assertGreater(aws["recommendation_score"], 0)
