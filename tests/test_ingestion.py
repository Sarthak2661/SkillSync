import unittest
from unittest.mock import Mock, patch

import requests

from src.ingestion.course_sources import CompositeCourseSource, YouTubeLearningSource
from src.ingestion.job_sources import (
    AdzunaJobsSource,
    ArbeitnowJobsSource,
    RemotiveJobsSource,
    parse_realpython_fake_jobs,
    parse_ycombinator_jobs,
)

class ParserTests(unittest.TestCase):
    def test_composite_course_source_continues_after_network_failure(self):
        unavailable = Mock()
        unavailable.fetch.side_effect = requests.RequestException("source unavailable")
        available = Mock()
        available.fetch.return_value = [Mock()]

        records = CompositeCourseSource([unavailable, available]).fetch()

        self.assertEqual(len(records), 1)
        available.fetch.assert_called_once_with()

    def test_parse_realpython_fake_jobs_card(self):
        html = """
        <div class="card-content">
          <h2 class="title">Data Engineer</h2>
          <h3 class="company">Example Analytics</h3>
          <p class="location">Remote</p>
          <time>2026-06-20</time>
          <footer>
            <a href="/apply">Apply</a>
            <a href="/jobs/data-engineer">Details</a>
          </footer>
        </div>
        """

        jobs = parse_realpython_fake_jobs(html, "https://example.com")

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].title, "Data Engineer")
        self.assertEqual(jobs[0].company, "Example Analytics")
        self.assertEqual(jobs[0].location, "Remote")
        self.assertEqual(jobs[0].url, "https://example.com/jobs/data-engineer")

    def test_parse_ycombinator_jobs_card(self):
        html = """
        <ul>
          <li>
            <a href="/companies/acme/jobs/abc123-data-engineer">Data Engineer</a>
            Acme AI (S24) &bull; Full-time &bull; $120K - $180K &bull; San Francisco / Remote
          </li>
        </ul>
        """

        jobs = parse_ycombinator_jobs(html, "https://www.ycombinator.com/jobs")

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].title, "Data Engineer")
        self.assertEqual(jobs[0].company, "Acme AI")
        self.assertEqual(jobs[0].salary_min, 120000)
        self.assertEqual(jobs[0].salary_max, 180000)
        self.assertEqual(
            jobs[0].url,
            "https://www.ycombinator.com/companies/acme/jobs/abc123-data-engineer",
        )


    def test_adzuna_without_credentials_skips_cleanly(self):
        self.assertEqual(AdzunaJobsSource().fetch(), [])

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

    def test_youtube_fallback_source_returns_learning_records(self):
        records = YouTubeLearningSource().fetch()

        self.assertGreaterEqual(len(records), 4)
        self.assertEqual(records[0].source_name, "youtube_learning")
        self.assertIn("youtube.com", records[0].payload["url"])
