from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from src.config.settings import settings
from src.domain.technology import TECHNOLOGY_JOB_SEARCH_TERMS, classify_role
from src.ingestion.base import RawRecord, SourceConnector, SourceFetchStatus, fetch_with_status, utc_now


class AdzunaJobsSource(SourceConnector):
    """Fetch real job postings from the official Adzuna API when credentials are configured."""

    source_name = "adzuna_jobs"
    source_type = "job_posting"

    def fetch(self) -> list[RawRecord]:
        if not settings.adzuna_app_id or not settings.adzuna_app_key:
            return []

        country = settings.adzuna_country.strip().lower() or "us"
        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
        per_query = _per_query_limit(settings.job_api_source_limit)
        rows: list[dict[str, object]] = []
        for search_term in TECHNOLOGY_JOB_SEARCH_TERMS:
            response = requests.get(
                url,
                params={
                    "app_id": settings.adzuna_app_id,
                    "app_key": settings.adzuna_app_key,
                    "what": search_term,
                    "results_per_page": per_query,
                    "content-type": "application/json",
                },
                headers={"User-Agent": settings.user_agent},
                timeout=25,
            )
            response.raise_for_status()
            rows.extend(response.json().get("results", []))
        rows = _dedupe_api_rows(rows)[: settings.job_api_source_limit]
        collected_at = utc_now()
        records: list[dict[str, object]] = []
        for row in rows:
            company = row.get("company") or {}
            location = row.get("location") or {}
            records.append(
                {
                    "external_id": str(row.get("id") or stable_text_id(row.get("title"), row.get("redirect_url"))),
                    "title": row.get("title") or "Unknown role",
                    "company": company.get("display_name") or "Unknown",
                    "location": location.get("display_name") or "Unknown",
                    "remote_type": infer_remote_type(str(location.get("display_name") or ""), str(row.get("description") or "")),
                    "salary_min": _safe_int(row.get("salary_min")),
                    "salary_max": _safe_int(row.get("salary_max")),
                    "description": html_to_text(row.get("description")),
                    "posted_at": row.get("created"),
                    "url": row.get("redirect_url") or url,
                }
            )
        return _raw_records(self.source_name, self.source_type, records, collected_at)


class ArbeitnowJobsSource(SourceConnector):
    """Fetch real job postings from the public Arbeitnow job board API."""

    source_name = "arbeitnow_jobs"
    source_type = "job_posting"
    url = "https://www.arbeitnow.com/api/job-board-api"

    def fetch(self) -> list[RawRecord]:
        response = requests.get(self.url, headers={"User-Agent": settings.user_agent}, timeout=25)
        response.raise_for_status()
        rows = [
            row
            for row in response.json().get("data", [])
            if _is_technology_job(str(row.get("title") or ""), html_to_text(row.get("description")))
        ][: settings.job_api_source_limit]
        collected_at = utc_now()
        records: list[dict[str, object]] = []
        for row in rows:
            description = html_to_text(row.get("description"))
            location = row.get("location") or "Unknown"
            records.append(
                {
                    "external_id": str(row.get("slug") or stable_text_id(row.get("title"), row.get("url"))),
                    "title": row.get("title") or "Unknown role",
                    "company": row.get("company_name") or "Unknown",
                    "location": location,
                    "remote_type": "Remote" if row.get("remote") else infer_remote_type(str(location), description),
                    "salary_min": None,
                    "salary_max": None,
                    "description": description,
                    "posted_at": _timestamp_to_iso(row.get("created_at")),
                    "url": row.get("url") or self.url,
                }
            )
        return _raw_records(self.source_name, self.source_type, records, collected_at)


class RemotiveJobsSource(SourceConnector):
    """Fetch real remote job postings from the official Remotive API."""

    source_name = "remotive_jobs"
    source_type = "job_posting"
    url = "https://remotive.com/api/remote-jobs"

    def fetch(self) -> list[RawRecord]:
        rows: list[dict[str, object]] = []
        for search_term in TECHNOLOGY_JOB_SEARCH_TERMS:
            response = requests.get(
                self.url,
                params={"search": search_term},
                headers={"User-Agent": settings.user_agent},
                timeout=25,
            )
            response.raise_for_status()
            rows.extend(response.json().get("jobs", []))
        rows = _dedupe_api_rows(rows)[: settings.job_api_source_limit]
        collected_at = utc_now()
        records: list[dict[str, object]] = []
        for row in rows:
            description = html_to_text(row.get("description"))
            location = row.get("candidate_required_location") or "Remote"
            records.append(
                {
                    "external_id": str(row.get("id") or stable_text_id(row.get("title"), row.get("url"))),
                    "title": row.get("title") or "Unknown role",
                    "company": row.get("company_name") or "Unknown",
                    "location": location,
                    "remote_type": "Remote",
                    "salary_min": None,
                    "salary_max": None,
                    "description": description,
                    "posted_at": row.get("publication_date"),
                    "url": row.get("url") or self.url,
                }
            )
        return _raw_records(self.source_name, self.source_type, records, collected_at)


class HackerNewsWhoIsHiringSource(SourceConnector):
    """Fetch technology-role posts from the latest HN Who's Hiring thread via Algolia."""

    source_name = "hackernews_who_is_hiring"
    source_type = "job_posting"
    api_url = "https://hn.algolia.com/api/v1"

    def fetch(self) -> list[RawRecord]:
        story = self._latest_hiring_story()
        if story is None:
            return []

        story_id = str(story["objectID"])
        response = requests.get(
            f"{self.api_url}/search_by_date",
            params={
                "tags": f"comment,story_{story_id}",
                "hitsPerPage": 1000,
            },
            headers={"User-Agent": settings.user_agent},
            timeout=25,
        )
        response.raise_for_status()
        hits = response.json().get("hits", [])
        collected_at = utc_now()
        records: list[dict[str, object]] = []

        for hit in hits:
            if not isinstance(hit, dict) or str(hit.get("parent_id")) != story_id:
                continue
            description = html_to_text(hit.get("comment_text"))
            if not _is_technology_role_post(description):
                continue

            object_id = str(hit.get("objectID") or stable_text_id(description))
            location = _hn_location(description)
            salary_min, salary_max = _salary_from_text(description)
            records.append(
                {
                    "external_id": object_id,
                    "title": _hn_role_title(description),
                    "company": _hn_company(hit.get("comment_text"), hit.get("author")),
                    "location": location,
                    "remote_type": infer_remote_type(location, description),
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "description": description,
                    "posted_at": hit.get("created_at"),
                    "url": f"https://news.ycombinator.com/item?id={object_id}",
                }
            )
            if len(records) >= settings.job_api_source_limit:
                break

        return _raw_records(self.source_name, self.source_type, records, collected_at)

    def _latest_hiring_story(self) -> dict[str, object] | None:
        response = requests.get(
            f"{self.api_url}/search_by_date",
            params={
                "tags": "story,author_whoishiring",
                "hitsPerPage": 12,
            },
            headers={"User-Agent": settings.user_agent},
            timeout=25,
        )
        response.raise_for_status()
        hits = response.json().get("hits", [])
        return next(
            (
                hit
                for hit in hits
                if isinstance(hit, dict)
                and hit.get("objectID")
                and "who is hiring" in str(hit.get("title") or "").lower()
            ),
            None,
        )


class CompositeJobSource(SourceConnector):
    source_name = "composite_job_sources"
    source_type = "job_posting"

    def __init__(self, sources: list[SourceConnector]) -> None:
        self.sources = sources
        self.fetch_statuses: list[SourceFetchStatus] = []

    def fetch(self) -> list[RawRecord]:
        records: list[RawRecord] = []
        self.fetch_statuses = []
        for source in self.sources:
            source_records, status = fetch_with_status(source, (requests.RequestException,))
            self.fetch_statuses.append(status)
            records.extend(source_records)
        return records


class StartupDataJobsSource(SourceConnector):
    """Small startup-style job feed used for repeatable local runs."""

    source_name = "startup_data_jobs"
    source_type = "job_posting"

    def fetch(self) -> list[RawRecord]:
        collected_at = utc_now()
        records = [
            {
                "external_id": "startup-job-001",
                "title": "Analytics Engineer",
                "company": "PulseMetrics",
                "location": "Remote",
                "remote_type": "Remote",
                "salary_min": 118000,
                "salary_max": 152000,
                "description": "Own dbt models, SQL transformations, Snowflake marts, Python data checks, and BI-ready semantic layers.",
                "posted_at": "2026-06-22",
                "url": "https://example.com/jobs/startup-analytics-engineer-001",
            },
            {
                "external_id": "startup-job-002",
                "title": "Product Data Scientist",
                "company": "SignalCart",
                "location": "San Francisco CA",
                "remote_type": "Hybrid",
                "salary_min": 140000,
                "salary_max": 185000,
                "description": "Use Python, SQL, statistics, A/B testing, forecasting, machine learning, and dashboards to explain product growth.",
                "posted_at": "2026-06-21",
                "url": "https://example.com/jobs/startup-product-data-scientist-002",
            },
            {
                "external_id": "startup-job-003",
                "title": "Data Platform Engineer",
                "company": "Lakehouse Labs",
                "location": "Austin TX",
                "remote_type": "Hybrid",
                "salary_min": 135000,
                "salary_max": 172000,
                "description": "Build Spark and Databricks pipelines with AWS, Docker, APIs, Airflow, data quality checks, and lakehouse governance.",
                "posted_at": "2026-06-19",
                "url": "https://example.com/jobs/startup-data-platform-engineer-003",
            },
        ]
        return _raw_records(self.source_name, self.source_type, records, collected_at)


class EnterpriseAnalyticsJobsSource(SourceConnector):
    """Small enterprise-style feed for BI, governance, and cloud analytics roles."""

    source_name = "enterprise_analytics_jobs"
    source_type = "job_posting"

    def fetch(self) -> list[RawRecord]:
        collected_at = utc_now()
        records = [
            {
                "external_id": "enterprise-job-001",
                "title": "Senior BI Developer",
                "company": "Northwind Financial",
                "location": "Chicago IL",
                "remote_type": "Hybrid",
                "salary_min": 105000,
                "salary_max": 138000,
                "description": "Develop Power BI dashboards, DAX measures, SQL Server models, data visualization standards, and executive KPI reporting.",
                "posted_at": "2026-06-20",
                "url": "https://example.com/jobs/enterprise-bi-developer-001",
            },
            {
                "external_id": "enterprise-job-002",
                "title": "Cloud Data Engineer",
                "company": "Orion Health Systems",
                "location": "Boston MA",
                "remote_type": "On-site",
                "salary_min": 128000,
                "salary_max": 164000,
                "description": "Deliver Azure Data Factory, Azure, SQL, Python, APIs, data modeling, ETL, and data quality controls for analytics teams.",
                "posted_at": "2026-06-18",
                "url": "https://example.com/jobs/enterprise-cloud-data-engineer-002",
            },
            {
                "external_id": "enterprise-job-003",
                "title": "Responsible AI Data Analyst",
                "company": "Civic Insight Group",
                "location": "Washington DC",
                "remote_type": "Remote",
                "salary_min": 98000,
                "salary_max": 126000,
                "description": "Analyze GenAI, LLMs, NLP, responsible AI, SQL, Python, data quality, model governance, and Tableau reporting workflows.",
                "posted_at": "2026-06-17",
                "url": "https://example.com/jobs/enterprise-responsible-ai-analyst-003",
            },
        ]
        return _raw_records(self.source_name, self.source_type, records, collected_at)


def _salary_from_text(text: str) -> tuple[int | None, int | None]:
    match = re.search(r"\$(\d+)(K)?\s*-\s*\$(\d+)(K)?", text, flags=re.IGNORECASE)
    if not match:
        return None, None
    low = int(match.group(1)) * (1000 if match.group(2) else 1)
    high = int(match.group(3)) * (1000 if match.group(4) else 1)
    return low, high


HN_TECHNOLOGY_ROLE_PATTERNS = (
    r"\bdata analyst\b",
    r"\bdata engineer\b",
    r"\bdata scientist\b",
    r"\banalytics engineer\b",
    r"\bbusiness intelligence\b",
    r"\bbi (?:analyst|developer|engineer)\b",
    r"\bmachine learning\b",
    r"\bmlops\b",
    r"\bdata platform\b",
    r"\bdata warehouse\b",
    r"\betl\b",
    r"\bdbt\b",
    r"\bairflow\b",
    r"\bsoftware (?:engineer|developer)\b",
    r"\b(?:front[ -]?end|back[ -]?end|full[ -]?stack) (?:engineer|developer)\b",
    r"\b(?:mobile|android|ios) (?:engineer|developer)\b",
    r"\b(?:devops|platform|cloud|site reliability) engineer\b",
    r"\b(?:database administrator|dba|database engineer)\b",
    r"\b(?:security|cybersecurity|soc) (?:engineer|analyst)\b",
    r"\b(?:network engineer|systems administrator|sysadmin)\b",
    r"\b(?:technology|technical|cloud|data|ai|ml) consultant\b",
    r"\b(?:java|javascript|typescript|react|node\.js|spring boot|\.net)\b",
    r"\b(?:kubernetes|terraform|linux|kafka|mongodb|redis)\b",
)

# Kept for callers that imported the original data-only name.
HN_DATA_ROLE_PATTERNS = HN_TECHNOLOGY_ROLE_PATTERNS

HN_ROLE_LABELS = (
    (r"\banalytics engineer\b", "Analytics Engineer"),
    (r"\bdata engineer\b", "Data Engineer"),
    (r"\bdata scientist\b", "Data Scientist"),
    (r"\bdata analyst\b", "Data Analyst"),
    (r"\bmachine learning engineer\b", "Machine Learning Engineer"),
    (r"\bmlops engineer\b", "MLOps Engineer"),
    (r"\bbi (?:analyst|developer|engineer)\b", "Business Intelligence Role"),
    (r"\bdata platform\b", "Data Platform Engineer"),
    (r"\bsoftware (?:engineer|developer)\b", "Software Engineer"),
    (r"\b(?:devops|platform|cloud) engineer\b", "Cloud and Platform Engineer"),
    (r"\b(?:database administrator|dba)\b", "Database Administrator"),
    (r"\b(?:security|cybersecurity) (?:engineer|analyst)\b", "Security Role"),
)


def _is_data_role_post(text: str) -> bool:
    """Backward-compatible alias for the broader technology-role check."""

    return _is_technology_role_post(text)


def _is_technology_role_post(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in HN_TECHNOLOGY_ROLE_PATTERNS)


def _hn_role_title(text: str) -> str:
    lowered = text.lower()
    for pattern, label in HN_ROLE_LABELS:
        if re.search(pattern, lowered):
            return label
    classification = classify_role(text)
    if classification.role_family != "Other Technology":
        return classification.role_name
    return "Technology Role"


def _hn_company(comment_html: object, author: object) -> str:
    lines = BeautifulSoup(str(comment_html or ""), "lxml").get_text("\n", strip=True).splitlines()
    if lines:
        company = re.split(r"\s*\|\s*", lines[0], maxsplit=1)[0].strip()
        if company and len(company) <= 100:
            return company
    return f"HN poster {author}" if author else "HN employer"


def _hn_location(text: str) -> str:
    parts = [part.strip() for part in text.split("|")[:4] if part.strip()]
    for part in parts[1:]:
        if re.search(r"\b(remote|hybrid|onsite|on-site)\b", part, flags=re.IGNORECASE):
            return part[:100]
    if re.search(r"\bremote\b", text, flags=re.IGNORECASE):
        return "Remote"
    return parts[1][:100] if len(parts) > 1 else "Unspecified"


def html_to_text(value: object) -> str:
    if value is None:
        return ""
    return BeautifulSoup(str(value), "lxml").get_text(" ", strip=True)


def stable_text_id(*parts: object) -> str:
    key = "|".join(str(part or "") for part in parts).lower()
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def _per_query_limit(total_limit: int) -> int:
    search_count = len(TECHNOLOGY_JOB_SEARCH_TERMS)
    return max(2, (max(total_limit, 1) + search_count - 1) // search_count)


def _dedupe_api_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    deduped: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in rows:
        key = str(
            row.get("id")
            or row.get("slug")
            or row.get("url")
            or row.get("redirect_url")
            or stable_text_id(row)
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _is_technology_job(title: str, description: str) -> bool:
    classification = classify_role(title)
    if classification.role_family != "Other Technology":
        return True
    text = f"{title} {description}".lower()
    return any(re.search(pattern, text) for pattern in HN_TECHNOLOGY_ROLE_PATTERNS)

def _safe_int(value: object) -> int | None:
    try:
        if value is None:
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _timestamp_to_iso(value: object) -> str | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).date().isoformat()
    except (TypeError, ValueError, OSError):
        return str(value)

def infer_remote_type(location: str, description: str) -> str:
    text = f"{location} {description}".lower()
    if re.search(r"\bremote\b", text):
        return "Remote"
    if re.search(r"\bhybrid\b", text):
        return "Hybrid"
    return "On-site"


def _raw_records(
    source_name: str,
    source_type: str,
    records: list[dict[str, object]],
    collected_at,
) -> list[RawRecord]:
    return [
        RawRecord(
            source_name=source_name,
            source_type=source_type,
            source_url=str(item["url"]),
            collected_at=collected_at,
            payload=item,
        )
        for item in records
    ]
