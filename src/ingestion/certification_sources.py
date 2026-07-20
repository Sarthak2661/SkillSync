from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import requests

from src.config.settings import settings
from src.ingestion.freecodecamp import FREECODECAMP_TRACKS, fetch_freecodecamp_tracks


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLOUD_CERTIFICATION_PATH = PROJECT_ROOT / "data" / "sample" / "cloud_certifications.json"

CREDENTIAL_SKILL_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Microsoft Fabric", ("microsoft fabric", "fabric data engineer")),
    ("Power BI", ("power bi", "business intelligence")),
    ("Machine Learning", ("machine learning", "ml engineer")),
    ("Data Pipelines", ("data engineering", "data engineer", "data pipeline")),
    ("Data Visualization", ("data visualization", "data visualisation")),
    ("Database Administration", ("database administrator", "database administration", "dba")),
    ("Kubernetes", ("kubernetes", "cloud native")),
    ("Terraform", ("terraform", "infrastructure as code")),
    ("Cybersecurity", ("cybersecurity", "cyber security", "information security")),
    ("Networking", ("network engineer", "network administration", "ccna")),
    ("Linux", ("linux", "system administrator", "system administration")),
    ("JavaScript", ("javascript", "web development")),
    ("React", ("react developer", "frontend development")),
    ("Software Engineering", ("software engineer", "software development")),
    ("ITIL", ("itil", "it service management")),
    ("SQL", ("sql", "relational database")),
    ("Python", ("python",)),
    ("AWS", ("aws", "amazon web services")),
    ("Azure", ("azure",)),
    ("GCP", ("google cloud", "gcp")),
)

TARGET_ROLES = {
    "Microsoft Fabric": "Fabric Data Engineer | Analytics Engineer",
    "Power BI": "Data Analyst | BI Analyst",
    "Machine Learning": "ML Engineer | Data Scientist",
    "Data Pipelines": "Data Engineer | Analytics Engineer",
    "Data Visualization": "Data Analyst | BI Analyst",
    "SQL": "Data Analyst | Data Engineer | Analytics Engineer",
    "Python": "Data Analyst | Data Scientist | Data Engineer",
    "AWS": "Cloud Data Engineer | Data Platform Engineer",
    "Azure": "Azure Data Engineer | Cloud Data Engineer",
    "GCP": "Cloud Data Engineer | Data Platform Engineer",
    "Database Administration": "Database Administrator | Database Reliability Engineer",
    "Kubernetes": "Platform Engineer | DevOps Engineer | Cloud Engineer",
    "Terraform": "Cloud Engineer | DevOps Engineer | Platform Engineer",
    "Cybersecurity": "Security Analyst | Security Engineer",
    "Networking": "Network Engineer | Network Administrator",
    "Linux": "Systems Administrator | Platform Engineer",
    "JavaScript": "Frontend Engineer | Full Stack Engineer",
    "React": "Frontend Engineer | Full Stack Engineer",
    "Software Engineering": "Software Engineer | Backend Engineer",
    "ITIL": "Technology Consultant | IT Service Manager",
}


class FreeCodeCampCertificationSource:
    source_name = "freecodecamp_curriculum"

    def __init__(self, session: Any = requests) -> None:
        self.session = session

    def fetch(self) -> list[dict[str, Any]]:
        verified = datetime.now(timezone.utc).date().isoformat()
        return [
            _freecodecamp_certification(track, self.source_name, "live_verified", verified)
            for track in fetch_freecodecamp_tracks(self.session)
        ]


class CredentialEngineCertificationSource:
    source_name = "credential_engine_registry"

    def __init__(self, session: Any = requests) -> None:
        self.session = session

    def fetch(self) -> list[dict[str, Any]]:
        if not settings.credential_engine_api_key:
            return []

        response = self.session.post(
            settings.credential_engine_api_url,
            headers={
                "Authorization": f"Bearer {settings.credential_engine_api_key}",
                "Content-Type": "application/json",
                "User-Agent": settings.user_agent,
            },
            json={
                "Skip": 0,
                "Take": min(settings.credential_engine_source_limit, 100),
                "Sort": "search:recordUpdated",
                "Query": {
                    "@type": ["ceterms:Certification", "ceterms:Certificate"],
                    "search:termGroup": {
                        "search:operator": "search:orTerms",
                        "ceterms:name": ["data", "software", "cloud", "database", "security", "network", "machine learning"],
                        "ceterms:description": ["data", "software", "cloud", "database", "security", "network", "machine learning"],
                    },
                },
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        resources = _result_rows(payload)
        verified = datetime.now(timezone.utc).date().isoformat()
        rows = [_normalize_credential_engine_record(resource, verified) for resource in resources]
        return [row for row in rows if row is not None]


def load_certification_catalog(mode: str | None = None) -> list[dict[str, Any]]:
    selected_mode = (mode or settings.certification_source_mode).strip().lower()
    if selected_mode not in {"curated", "freecodecamp", "credential_engine", "all"}:
        raise ValueError(
            f"Unsupported certification source mode '{selected_mode}'. "
            "Use 'curated', 'freecodecamp', 'credential_engine', or 'all'."
        )

    rows = _load_cloud_certifications()
    if selected_mode in {"freecodecamp", "all"}:
        try:
            rows.extend(FreeCodeCampCertificationSource().fetch())
        except (requests.RequestException, ValueError):
            rows.extend(_freecodecamp_snapshot())
    else:
        rows.extend(_freecodecamp_snapshot())

    if selected_mode in {"credential_engine", "all"} and settings.credential_engine_api_key:
        try:
            rows.extend(CredentialEngineCertificationSource().fetch())
        except (requests.RequestException, ValueError):
            pass
    return rows


def _load_cloud_certifications() -> list[dict[str, Any]]:
    with CLOUD_CERTIFICATION_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("Cloud certification catalog must contain a JSON list.")
    return [row for row in payload if isinstance(row, dict)]


def _freecodecamp_snapshot() -> list[dict[str, Any]]:
    return [
        _freecodecamp_certification(track, "freecodecamp_curriculum_snapshot", "curated_demo", "2026-07-19")
        for track in FREECODECAMP_TRACKS
    ]


def _freecodecamp_certification(
    track: dict[str, str],
    source_name: str,
    confidence: str,
    verified: str,
) -> dict[str, Any]:
    return {
        "skill": track["skill"],
        "certification_name": f"freeCodeCamp {track['title']}",
        "provider": "freeCodeCamp",
        "level": "Beginner",
        "free_or_paid": "Free",
        "estimated_cost_usd": 0,
        "target_roles": TARGET_ROLES.get(track["skill"], "Technology professional"),
        "url": f"https://www.freecodecamp.org/learn/{track['slug']}/",
        "priority_score": 76,
        "source_name": source_name,
        "source_confidence": confidence,
        "last_verified": verified,
    }


def _result_rows(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise ValueError("Credential Engine response was not a JSON object.")
    rows = payload.get("Results") or payload.get("results") or []
    if not isinstance(rows, list):
        raise ValueError("Credential Engine response did not contain a result list.")
    output: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        resource = row.get("Resource") or row.get("resource") or row
        if isinstance(resource, dict):
            output.append(resource)
    return output


def _normalize_credential_engine_record(resource: dict[str, Any], verified: str) -> dict[str, Any] | None:
    name = _text_value(resource.get("ceterms:name") or resource.get("name"))
    description = _text_value(resource.get("ceterms:description") or resource.get("description"))
    skill = _match_skill(f"{name} {description}")
    if not name or not skill:
        return None

    provider = _organization_name(
        resource.get("ceterms:ownedBy")
        or resource.get("ceterms:offeredBy")
        or resource.get("ownedBy")
        or resource.get("offeredBy")
    )
    url = _text_value(resource.get("ceterms:subjectWebpage") or resource.get("subjectWebpage"))
    url = url or str(resource.get("@id") or "https://credentialfinder.org/")
    return {
        "skill": skill,
        "certification_name": name,
        "provider": provider or "Credential Engine publisher",
        "level": "Not listed",
        "free_or_paid": "Not listed",
        "estimated_cost_usd": None,
        "target_roles": TARGET_ROLES.get(skill, "Technology professional"),
        "url": url,
        "priority_score": 72,
        "source_name": "credential_engine_registry",
        "source_confidence": "live_verified",
        "last_verified": verified,
    }


def _match_skill(text: str) -> str | None:
    normalized = text.lower()
    for skill, keywords in CREDENTIAL_SKILL_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return skill
    return None


def _text_value(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        for item in value:
            text = _text_value(item)
            if text:
                return text
        return ""
    if isinstance(value, dict):
        for key in ("en", "en-US", "@value", "name", "ceterms:name"):
            text = _text_value(value.get(key))
            if text:
                return text
        for item in value.values():
            text = _text_value(item)
            if text:
                return text
        return ""
    return ""


def _organization_name(value: Any) -> str:
    if isinstance(value, list):
        for item in value:
            name = _organization_name(item)
            if name:
                return name
        return ""
    if isinstance(value, dict):
        return _text_value(value.get("ceterms:name") or value.get("name"))
    return ""
