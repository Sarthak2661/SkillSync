from __future__ import annotations

from typing import Any

import requests

from src.config.settings import settings


FREECODECAMP_CERTIFICATIONS_URL = (
    "https://api.github.com/repos/freeCodeCamp/freeCodeCamp/contents/"
    "curriculum/challenges/english/certifications"
)

FREECODECAMP_TRACKS: tuple[dict[str, str], ...] = (
    {
        "filename": "python-v9.yml",
        "slug": "python-v9",
        "title": "Python Certification",
        "skill": "Python",
        "subjects": "python|programming|data-analysis",
        "roles": "data-analyst|data-engineer|data-scientist",
        "products": "python",
    },
    {
        "filename": "relational-databases-v9.yml",
        "slug": "relational-databases-v9",
        "title": "Relational Databases Certification",
        "skill": "SQL",
        "subjects": "sql|relational-databases|postgresql",
        "roles": "data-analyst|data-engineer|analytics-engineer",
        "products": "sql|postgresql",
    },
    {
        "filename": "data-analysis-with-python.yml",
        "slug": "data-analysis-with-python",
        "title": "Data Analysis with Python Certification",
        "skill": "pandas",
        "subjects": "python|pandas|numpy|data-analysis",
        "roles": "data-analyst|data-scientist",
        "products": "python|pandas|numpy",
    },
    {
        "filename": "data-visualization.yml",
        "slug": "data-visualization",
        "title": "Data Visualization Certification",
        "skill": "Data Visualization",
        "subjects": "data-visualization|d3|dashboards",
        "roles": "data-analyst|bi-analyst",
        "products": "d3",
    },
    {
        "filename": "machine-learning-with-python.yml",
        "slug": "machine-learning-with-python",
        "title": "Machine Learning with Python Certification",
        "skill": "Machine Learning",
        "subjects": "machine-learning|python|tensorflow",
        "roles": "data-scientist|ml-engineer",
        "products": "python|tensorflow",
    },
    {
        "filename": "back-end-development-and-apis-v9.yml",
        "slug": "back-end-development-and-apis-v9",
        "title": "Back End Development and APIs Certification",
        "skill": "APIs",
        "subjects": "apis|backend-development|databases",
        "roles": "data-engineer|backend-data-engineer",
        "products": "apis",
    },
    {
        "filename": "responsive-web-design-v9.yml",
        "slug": "responsive-web-design-v9",
        "title": "Responsive Web Design Certification",
        "skill": "HTML",
        "subjects": "html|css|responsive-web-design|accessibility",
        "roles": "frontend-engineer|full-stack-engineer",
        "products": "html|css",
    },
    {
        "filename": "javascript-algorithms-and-data-structures-v8.yml",
        "slug": "javascript-algorithms-and-data-structures-v8",
        "title": "JavaScript Algorithms and Data Structures Certification",
        "skill": "JavaScript",
        "subjects": "javascript|algorithms|data-structures|programming",
        "roles": "frontend-engineer|full-stack-engineer|software-engineer",
        "products": "javascript",
    },
    {
        "filename": "front-end-development-libraries.yml",
        "slug": "front-end-development-libraries",
        "title": "Front End Development Libraries Certification",
        "skill": "React",
        "subjects": "react|frontend|javascript|web-development",
        "roles": "frontend-engineer|full-stack-engineer",
        "products": "react|javascript",
    },
    {
        "filename": "information-security-v7.yml",
        "slug": "information-security",
        "title": "Information Security Certification",
        "skill": "Cybersecurity",
        "subjects": "cybersecurity|information-security|python|secure-development",
        "roles": "security-analyst|security-engineer",
        "products": "python",
    },
    {
        "filename": "quality-assurance-v7.yml",
        "slug": "quality-assurance",
        "title": "Quality Assurance Certification",
        "skill": "Test Automation",
        "subjects": "quality-assurance|test-automation|javascript|apis",
        "roles": "qa-automation-engineer|software-engineer",
        "products": "javascript|apis",
    },
)

# Compatibility alias for older imports.
FREECODECAMP_DATA_TRACKS = FREECODECAMP_TRACKS


def fetch_freecodecamp_tracks(session: Any = requests) -> list[dict[str, str]]:
    response = session.get(
        FREECODECAMP_CERTIFICATIONS_URL,
        headers=github_headers(),
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("freeCodeCamp curriculum response was not a directory listing.")

    files = {
        str(item.get("name")): item
        for item in payload
        if isinstance(item, dict) and item.get("type") == "file"
    }
    tracks: list[dict[str, str]] = []
    for definition in FREECODECAMP_TRACKS:
        item = files.get(definition["filename"])
        if not item:
            continue
        row = dict(definition)
        row["repository_url"] = str(item.get("html_url") or "")
        row["repository_path"] = str(item.get("path") or "")
        tracks.append(row)
    return tracks


def github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": settings.user_agent,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers
