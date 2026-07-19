from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
from threading import Lock
import time
from typing import Any

import requests

from src.config.settings import settings


GITHUB_API = "https://api.github.com"
_CACHE: dict[tuple[str, int], tuple[float, "PracticeResult"]] = {}
_CACHE_LOCK = Lock()
TOPIC_ALIASES = {
    "Airflow": "apache-airflow",
    "AWS": "aws",
    "Azure": "azure",
    "Azure Data Factory": "azure-data-factory",
    "Data Visualization": "data-visualization",
    "dbt": "dbt",
    "Deep Learning": "deep-learning",
    "GCP": "google-cloud",
    "GenAI": "generative-ai",
    "LLMs": "large-language-models",
    "Machine Learning": "machine-learning",
    "Microsoft Fabric": "microsoft-fabric",
    "NLP": "natural-language-processing",
    "NoSQL": "nosql",
    "Power BI": "power-bi",
    "Responsible AI": "responsible-ai",
    "SQL Server": "sql-server",
}


@dataclass(frozen=True)
class PracticeResult:
    skill: str
    topic: str
    items: list[dict[str, Any]]
    fetched_at: str
    authenticated: bool
    rate_limit_remaining: int | None
    status: str
    message: str = ""


class GitHubPracticeClient:
    def __init__(self, token: str | None = None, session: requests.Session | None = None) -> None:
        self.token = token
        self.session = session or requests.Session()

    def recommend(self, skill: str, limit: int = 8, repository_limit: int = 5) -> PracticeResult:
        topic = topic_for_skill(skill)
        fetched_at = datetime.now(timezone.utc).isoformat()
        try:
            repositories, remaining = self._find_repositories(topic, repository_limit)
            issues = self._find_issues(repositories, skill, limit)
        except requests.RequestException as exc:
            return PracticeResult(
                skill=skill,
                topic=topic,
                items=[],
                fetched_at=fetched_at,
                authenticated=bool(self.token),
                rate_limit_remaining=_remaining_from_error(exc),
                status="unavailable",
                message=_friendly_error(exc),
            )

        message = "" if issues else f"No open beginner-friendly issues were found in recently updated {topic} repositories."
        return PracticeResult(
            skill=skill,
            topic=topic,
            items=issues,
            fetched_at=fetched_at,
            authenticated=bool(self.token),
            rate_limit_remaining=remaining,
            status="ok",
            message=message,
        )

    def _find_repositories(self, topic: str, limit: int) -> tuple[list[dict[str, Any]], int | None]:
        pushed_after = (datetime.now(timezone.utc) - timedelta(days=settings.github_updated_within_days)).date()
        response = self.session.get(
            f"{GITHUB_API}/search/repositories",
            headers=self._headers(),
            params={
                "q": f"topic:{topic} archived:false pushed:>={pushed_after}",
                "sort": "stars",
                "order": "desc",
                "per_page": limit,
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json().get("items", []), _remaining(response)

    def _find_issues(
        self,
        repositories: list[dict[str, Any]],
        skill: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        seen: set[str] = set()
        for label in ("good first issue", "help wanted"):
            for repository in repositories:
                if len(output) >= limit:
                    break
                response = self.session.get(
                    f"{GITHUB_API}/repos/{repository['full_name']}/issues",
                    headers=self._headers(),
                    params={
                        "state": "open",
                        "labels": label,
                        "sort": "updated",
                        "direction": "desc",
                        "per_page": min(10, limit),
                    },
                    timeout=15,
                )
                response.raise_for_status()
                for issue in response.json():
                    if "pull_request" in issue or issue["html_url"] in seen:
                        continue
                    seen.add(issue["html_url"])
                    output.append(_normalize_issue(skill, label, repository, issue))
                    if len(output) >= limit:
                        break
            if len(output) >= limit:
                break
        return output

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": settings.user_agent,
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers


def recommend_practice_projects(skill: str, limit: int = 8) -> PracticeResult:
    key = (skill.strip().lower(), limit)
    now = time.monotonic()
    with _CACHE_LOCK:
        cached = _CACHE.get(key)
        if cached and cached[0] > now:
            return cached[1]

    result = GitHubPracticeClient(settings.github_token).recommend(
        skill=skill,
        limit=limit,
        repository_limit=settings.github_repository_limit,
    )
    ttl_seconds = settings.github_cache_minutes * 60 if result.status == "ok" else 60
    with _CACHE_LOCK:
        _CACHE[key] = (now + ttl_seconds, result)
    return result


def topic_for_skill(skill: str) -> str:
    if skill in TOPIC_ALIASES:
        return TOPIC_ALIASES[skill]
    topic = re.sub(r"[^a-z0-9]+", "-", skill.lower()).strip("-")
    return topic or "data-engineering"


def _normalize_issue(
    skill: str,
    practice_label: str,
    repository: dict[str, Any],
    issue: dict[str, Any],
) -> dict[str, Any]:
    labels = [label["name"] if isinstance(label, dict) else str(label) for label in issue.get("labels", [])]
    return {
        "skill": skill,
        "repository": repository["full_name"],
        "repository_url": repository["html_url"],
        "repository_description": repository.get("description"),
        "repository_topics": " | ".join(repository.get("topics", [])),
        "language": repository.get("language"),
        "stars": repository.get("stargazers_count", 0),
        "repository_updated_at": repository.get("updated_at"),
        "issue_number": issue["number"],
        "issue_title": issue["title"],
        "issue_url": issue["html_url"],
        "issue_labels": " | ".join(labels),
        "practice_label": practice_label,
        "issue_updated_at": issue.get("updated_at"),
        "source_name": "github_public_api",
        "source_confidence": "live_verified",
    }


def _remaining(response: requests.Response) -> int | None:
    value = response.headers.get("X-RateLimit-Remaining")
    return int(value) if value and value.isdigit() else None


def _remaining_from_error(error: requests.RequestException) -> int | None:
    return _remaining(error.response) if error.response is not None else None


def _friendly_error(error: requests.RequestException) -> str:
    response = error.response
    if response is not None and response.status_code in {403, 429}:
        reset = response.headers.get("X-RateLimit-Reset")
        if reset and reset.isdigit():
            reset_at = datetime.fromtimestamp(int(reset), tz=timezone.utc).isoformat()
            return f"GitHub API rate limit reached. Try again after {reset_at}."
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            return f"GitHub API rate limit reached. Try again in {retry_after} seconds."
        return "GitHub API rate limit reached. Add MARKET_INTEL_GITHUB_TOKEN for a higher limit."
    return f"GitHub API request failed: {error}"
