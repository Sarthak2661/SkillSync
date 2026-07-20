from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from typing import Any
from urllib.parse import urlparse

import requests

from src.config.settings import settings
from src.ingestion.base import RawRecord, SourceConnector, utc_now
from src.ingestion.freecodecamp import fetch_freecodecamp_tracks, github_headers


GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

LEARNING_PATH_TOPICS: tuple[dict[str, str], ...] = (
    {
        "skill": "Data Pipelines",
        "topic": "data-engineering",
        "subjects": "data-engineering|etl|data-pipelines",
        "roles": "data-engineer|analytics-engineer",
    },
    {
        "skill": "Airflow",
        "topic": "apache-airflow",
        "subjects": "airflow|orchestration|data-pipelines",
        "roles": "data-engineer|analytics-engineer",
    },
    {
        "skill": "dbt",
        "topic": "dbt",
        "subjects": "dbt|sql|analytics-engineering",
        "roles": "analytics-engineer|data-engineer",
    },
    {
        "skill": "Machine Learning",
        "topic": "machine-learning",
        "subjects": "machine-learning|python|modeling",
        "roles": "data-scientist|ml-engineer",
    },
    {
        "skill": "Power BI",
        "topic": "power-bi",
        "subjects": "power-bi|business-intelligence|data-visualization",
        "roles": "data-analyst|bi-analyst",
    },
    {
        "skill": "Snowflake",
        "topic": "snowflake",
        "subjects": "snowflake|data-warehouse|sql",
        "roles": "data-engineer|analytics-engineer",
    },
    {
        "skill": "Kubernetes",
        "topic": "kubernetes",
        "subjects": "kubernetes|containers|cloud|devops",
        "roles": "platform-engineer|devops-engineer|cloud-engineer",
    },
    {
        "skill": "Terraform",
        "topic": "terraform",
        "subjects": "terraform|infrastructure-as-code|cloud|devops",
        "roles": "cloud-engineer|devops-engineer|platform-engineer",
    },
    {
        "skill": "Cybersecurity",
        "topic": "cybersecurity",
        "subjects": "cybersecurity|information-security|secure-development",
        "roles": "security-analyst|security-engineer",
    },
    {
        "skill": "Software Engineering",
        "topic": "software-engineering",
        "subjects": "software-engineering|programming|architecture",
        "roles": "software-engineer|backend-engineer|frontend-engineer",
    },
)


class FreeCodeCampCurriculumSource(SourceConnector):
    """Read technology curriculum tracks from freeCodeCamp's official GitHub index."""

    source_name = "freecodecamp_curriculum"
    source_type = "course_listing"

    def __init__(self, session: Any = requests) -> None:
        self.session = session

    def fetch(self) -> list[RawRecord]:
        collected_at = utc_now()
        records: list[RawRecord] = []
        for track in fetch_freecodecamp_tracks(self.session):
            course_url = f"https://www.freecodecamp.org/learn/{track['slug']}/"
            records.append(
                RawRecord(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    source_url=track.get("repository_url") or course_url,
                    collected_at=collected_at,
                    payload={
                        "external_id": f"freecodecamp-{track['slug']}",
                        "title": track["title"],
                        "platform": "freeCodeCamp Curriculum",
                        "level": "Self-paced",
                        "rating": None,
                        "duration_minutes": None,
                        "description": f"Project-based freeCodeCamp curriculum for {track['skill']}.",
                        "subjects": track["subjects"],
                        "roles": track["roles"],
                        "products": track["products"],
                        "last_modified": None,
                        "url": course_url,
                    },
                )
            )
        return records


class GitHubLearningPathSource(SourceConnector):
    """Find maintained awesome lists and roadmaps using GitHub's official API."""

    source_name = "github_learning_paths"
    source_type = "course_listing"

    def __init__(self, session: Any = requests) -> None:
        self.session = session

    def fetch(self) -> list[RawRecord]:
        collected_at = utc_now()
        pushed_after = (datetime.now(timezone.utc) - timedelta(days=settings.github_updated_within_days)).date()
        records: list[RawRecord] = []
        last_error: requests.RequestException | None = None

        for topic in LEARNING_PATH_TOPICS[: settings.github_learning_path_limit]:
            try:
                response = self.session.get(
                    GITHUB_SEARCH_URL,
                    headers=github_headers(),
                    params={
                        "q": (
                            f"awesome {topic['topic']} in:name,description archived:false "
                            f"stars:>={settings.github_learning_path_min_stars} pushed:>={pushed_after}"
                        ),
                        "sort": "stars",
                        "order": "desc",
                        "per_page": 5,
                    },
                    timeout=20,
                )
                response.raise_for_status()
            except requests.RequestException as exc:
                last_error = exc
                continue

            payload = response.json()
            if not isinstance(payload, dict):
                continue
            for repository in payload.get("items", []):
                row = _normalize_learning_repository(topic, repository)
                if row is None:
                    continue
                records.append(
                    RawRecord(
                        source_name=self.source_name,
                        source_type=self.source_type,
                        source_url=row["url"],
                        collected_at=collected_at,
                        payload=row,
                    )
                )
                break

        if not records and last_error is not None:
            raise last_error
        return records


def _normalize_learning_repository(topic: dict[str, str], repository: Any) -> dict[str, Any] | None:
    if not isinstance(repository, dict) or repository.get("archived"):
        return None

    full_name = str(repository.get("full_name") or "")
    name = str(repository.get("name") or "")
    url = str(repository.get("html_url") or "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", full_name):
        return None
    if not ({"awesome", "roadmap"} & set(re.split(r"[-_.]", name.lower()))):
        return None
    if urlparse(url).netloc.lower() != "github.com":
        return None

    return {
        "external_id": f"github-learning-{repository.get('id') or full_name}",
        "title": f"{topic['skill']} learning path: {full_name}",
        "platform": "GitHub Learning Paths",
        "level": "Community curated",
        "rating": None,
        "duration_minutes": None,
        "description": f"Recently maintained curated repository for learning {topic['skill']}.",
        "subjects": topic["subjects"],
        "roles": topic["roles"],
        "products": topic["topic"],
        "last_modified": repository.get("pushed_at"),
        "url": url,
    }
