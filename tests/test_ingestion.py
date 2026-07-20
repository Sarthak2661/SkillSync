import unittest
from unittest.mock import Mock, patch

import requests

from src.ingestion.course_sources import CompositeCourseSource, OfficialLearningCatalogSource, YouTubeLearningSource
from src.ingestion.curated_job_source import CuratedTechnologyJobsSource
from src.ingestion.job_sources import (
    AdzunaJobsSource,
    ArbeitnowJobsSource,
    CompositeJobSource,
    HackerNewsWhoIsHiringSource,
    RemotiveJobsSource,
)

class IngestionSourceTests(unittest.TestCase):
    def test_composite_course_source_continues_after_network_failure(self):
        unavailable = Mock()
        unavailable.source_name = "unavailable_courses"
        unavailable.source_type = "course_listing"
        unavailable.fetch.side_effect = requests.RequestException("source unavailable")
        available = Mock()
        available.source_name = "available_courses"
        available.source_type = "course_listing"
        available.fetch.return_value = [Mock()]

        source = CompositeCourseSource([unavailable, available])
        records = source.fetch()

        self.assertEqual(len(records), 1)
        available.fetch.assert_called_once_with()
        self.assertEqual([status.status for status in source.fetch_statuses], ["failed", "success"])
        self.assertEqual(source.fetch_statuses[0].error_type, "RequestException")

    def test_composite_job_source_records_empty_and_success_statuses(self):
        empty = Mock()
        empty.source_name = "empty_jobs"
        empty.source_type = "job_posting"
        empty.fetch.return_value = []
        available = Mock()
        available.source_name = "available_jobs"
        available.source_type = "job_posting"
        available.fetch.return_value = [Mock()]

        source = CompositeJobSource([empty, available])
        records = source.fetch()

        self.assertEqual(len(records), 1)
        self.assertEqual([status.status for status in source.fetch_statuses], ["empty", "success"])
        self.assertEqual([status.record_count for status in source.fetch_statuses], [0, 1])
    def test_adzuna_without_credentials_skips_cleanly(self):
        self.assertEqual(AdzunaJobsSource().fetch(), [])
    def test_curated_technology_source_has_broad_role_coverage(self):
        records = CuratedTechnologyJobsSource().fetch()
        titles = " ".join(str(record.payload.get("title") or "") for record in records)

        self.assertGreaterEqual(len(records), 30)
        for expected in ["Backend", "Machine Learning", "DevOps", "Database Administrator", "Security", "Consultant"]:
            self.assertIn(expected, titles)


    @patch("src.ingestion.job_sources.requests.get")
    def test_arbeitnow_api_returns_job_records(self, mock_get):
        response = Mock()
        response.json.return_value = {
            "data": [
                {
                    "slug": "data-engineer-remote",
                    "company_name": "Example API Co",
                    "title": "Data Engineer",
                    "description": "<p>Build Python and SQL pipelines.</p>",
                    "remote": True,
                    "location": "Remote",
                    "created_at": 1783296000,
                    "url": "https://www.arbeitnow.com/jobs/data-engineer-remote",
                }
            ]
        }
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        records = ArbeitnowJobsSource().fetch()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source_name, "arbeitnow_jobs")
        self.assertEqual(records[0].payload["remote_type"], "Remote")
        self.assertIn("Python", records[0].payload["description"])

    @patch("src.ingestion.job_sources.requests.get")
    def test_remotive_api_returns_job_records(self, mock_get):
        response = Mock()
        response.json.return_value = {
            "jobs": [
                {
                    "id": 123,
                    "company_name": "Remote Data Co",
                    "title": "Analytics Engineer",
                    "description": "<p>SQL, dbt, and warehouse work.</p>",
                    "candidate_required_location": "Worldwide",
                    "publication_date": "2026-07-18T00:00:00",
                    "url": "https://remotive.com/remote-jobs/data/analytics-engineer-123",
                }
            ]
        }
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        records = RemotiveJobsSource().fetch()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source_name, "remotive_jobs")
        self.assertEqual(records[0].payload["remote_type"], "Remote")
        self.assertIn("dbt", records[0].payload["description"])

    @patch("src.ingestion.job_sources.requests.get")
    def test_hackernews_api_keeps_top_level_technology_job_posts(self, mock_get):
        story_response = Mock()
        story_response.json.return_value = {
            "hits": [{"objectID": "456", "title": "Ask HN: Who is hiring? (July 2026)"}]
        }
        story_response.raise_for_status.return_value = None

        comments_response = Mock()
        comments_response.json.return_value = {
            "hits": [
                {
                    "objectID": "9001",
                    "parent_id": 456,
                    "author": "hiring_manager",
                    "created_at": "2026-07-01T12:00:00Z",
                    "comment_text": (
                        "<p>Signal Works | Remote | $120K - $160K</p>"
                        "<p>Hiring a Data Engineer to build Python, SQL, dbt, and Airflow pipelines.</p>"
                    ),
                },
                {
                    "objectID": "9002",
                    "parent_id": 456,
                    "author": "founder",
                    "created_at": "2026-07-01T12:10:00Z",
                    "comment_text": "<p>Hiring a product designer for our mobile app.</p>",
                },
                {
                    "objectID": "9003",
                    "parent_id": 9001,
                    "author": "candidate",
                    "created_at": "2026-07-01T12:20:00Z",
                    "comment_text": "<p>Is the Data Engineer role available in Canada?</p>",
                },
            ]
        }
        comments_response.raise_for_status.return_value = None
        mock_get.side_effect = [story_response, comments_response]

        records = HackerNewsWhoIsHiringSource().fetch()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source_name, "hackernews_who_is_hiring")
        self.assertEqual(records[0].payload["company"], "Signal Works")
        self.assertEqual(records[0].payload["title"], "Data Engineer")
        self.assertEqual(records[0].payload["remote_type"], "Remote")
        self.assertEqual(records[0].payload["salary_min"], 120000)
        self.assertEqual(records[0].payload["salary_max"], 160000)
        self.assertEqual(records[0].payload["url"], "https://news.ycombinator.com/item?id=9001")
        self.assertEqual(mock_get.call_args_list[0].kwargs["params"]["tags"], "story,author_whoishiring")
        self.assertEqual(mock_get.call_args_list[1].kwargs["params"]["hitsPerPage"], 1000)

    def test_official_learning_catalog_has_verified_breadth(self):
        records = OfficialLearningCatalogSource().fetch()

        self.assertGreaterEqual(len(records), 30)
        self.assertEqual({record.source_name for record in records}, {"official_learning_catalog"})
        self.assertTrue(all(record.payload["url"].startswith("https://") for record in records))

    def test_youtube_fallback_source_returns_learning_records(self):
        records = YouTubeLearningSource().fetch()

        self.assertGreaterEqual(len(records), 4)
        self.assertEqual(records[0].source_name, "youtube_learning")
        self.assertIn("youtube.com", records[0].payload["url"])
