import unittest
from unittest.mock import Mock

import requests

from src.analytics.github_practice import GitHubPracticeClient, topic_for_skill


def response(payload, remaining="42"):
    item = Mock()
    item.json.return_value = payload
    item.headers = {"X-RateLimit-Remaining": remaining}
    item.raise_for_status.return_value = None
    return item


class GitHubPracticeTests(unittest.TestCase):
    def test_topic_aliases_and_slug_fallback(self):
        self.assertEqual(topic_for_skill("Power BI"), "power-bi")
        self.assertEqual(topic_for_skill("Apache Kafka"), "apache-kafka")

    def test_recommender_normalizes_open_issue(self):
        repository = {
            "full_name": "example/dbt-project",
            "html_url": "https://github.com/example/dbt-project",
            "description": "Practice analytics engineering",
            "topics": ["dbt", "analytics-engineering"],
            "language": "SQL",
            "stargazers_count": 120,
            "updated_at": "2026-07-17T10:00:00Z",
        }
        issue = {
            "number": 12,
            "title": "Add a staging model",
            "html_url": "https://github.com/example/dbt-project/issues/12",
            "labels": [{"name": "good first issue"}],
            "updated_at": "2026-07-18T10:00:00Z",
        }
        session = Mock()
        session.get.side_effect = [response({"items": [repository]}), response([issue])]

        result = GitHubPracticeClient(token="token", session=session).recommend("dbt", limit=1)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.topic, "dbt")
        self.assertEqual(result.items[0]["practice_label"], "good first issue")
        self.assertEqual(result.items[0]["source_confidence"], "live_verified")
        first_call = session.get.call_args_list[0]
        self.assertIn("topic:dbt", first_call.kwargs["params"]["q"])
        self.assertIn("Authorization", first_call.kwargs["headers"])

    def test_pull_requests_are_excluded(self):
        repository = {
            "full_name": "example/airflow",
            "html_url": "https://github.com/example/airflow",
            "topics": ["apache-airflow"],
            "stargazers_count": 10,
        }
        pull_request = {
            "number": 4,
            "title": "Already submitted",
            "html_url": "https://github.com/example/airflow/pull/4",
            "labels": [{"name": "good first issue"}],
            "pull_request": {"url": "https://api.github.com/pulls/4"},
        }
        session = Mock()
        session.get.side_effect = [response({"items": [repository]}), response([pull_request]), response([])]

        result = GitHubPracticeClient(session=session).recommend("Airflow", limit=1)

        self.assertEqual(result.items, [])
        self.assertIn("No open beginner-friendly issues", result.message)

    def test_rate_limit_returns_actionable_status(self):
        failed = Mock()
        failed.headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "2000000000"}
        failed.status_code = 403
        error = requests.HTTPError("rate limited")
        error.response = failed
        session = Mock()
        session.get.return_value.raise_for_status.side_effect = error

        result = GitHubPracticeClient(session=session).recommend("dbt")

        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.rate_limit_remaining, 0)
        self.assertIn("Try again after", result.message)


if __name__ == "__main__":
    unittest.main()
