from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.config.settings import settings
from src.ingestion.base import RawRecord, SourceConnector, utc_now


@dataclass(frozen=True)
class ScrapedJobPosting:
    title: str
    company: str
    location: str
    description: str
    url: str
    posted_at: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None


class RealPythonFakeJobsSource(SourceConnector):
    """Scrape a stable public HTML job board used for scraping practice."""

    source_name = "realpython_fake_jobs"
    source_type = "job_posting"

    def __init__(self, url: str | None = None) -> None:
        self.url = url or settings.job_source_url

    def fetch(self) -> list[RawRecord]:
        html = self._fetch_html(self.url)
        postings = parse_realpython_fake_jobs(html, self.url)
        collected_at = utc_now()

        return [
            RawRecord(
                source_name=self.source_name,
                source_type=self.source_type,
                source_url=posting.url,
                collected_at=collected_at,
                payload={
                    "external_id": stable_job_id(posting),
                    "title": posting.title,
                    "company": posting.company,
                    "location": posting.location,
                    "remote_type": infer_remote_type(posting.location, posting.description),
                    "salary_min": posting.salary_min,
                    "salary_max": posting.salary_max,
                    "description": posting.description,
                    "posted_at": posting.posted_at,
                    "url": posting.url,
                },
            )
            for posting in postings
        ]

    def _fetch_html(self, url: str) -> str:
        response = requests.get(
            url,
            headers={"User-Agent": settings.user_agent},
            timeout=20,
        )
        response.raise_for_status()
        return response.text


class YCombinatorJobsSource(SourceConnector):
    """Scrape public Y Combinator startup job cards."""

    source_name = "ycombinator_jobs"
    source_type = "job_posting"
    url = "https://www.ycombinator.com/jobs"

    def fetch(self) -> list[RawRecord]:
        html = self._fetch_html(self.url)
        postings = parse_ycombinator_jobs(html, self.url)
        collected_at = utc_now()

        return [
            RawRecord(
                source_name=self.source_name,
                source_type=self.source_type,
                source_url=posting.url,
                collected_at=collected_at,
                payload={
                    "external_id": stable_job_id(posting),
                    "title": posting.title,
                    "company": posting.company,
                    "location": posting.location,
                    "remote_type": infer_remote_type(posting.location, posting.description),
                    "salary_min": posting.salary_min,
                    "salary_max": posting.salary_max,
                    "description": posting.description,
                    "posted_at": posting.posted_at,
                    "url": posting.url,
                },
            )
            for posting in postings
        ]

    def _fetch_html(self, url: str) -> str:
        response = requests.get(
            url,
            headers={"User-Agent": settings.user_agent},
            timeout=30,
        )
        response.raise_for_status()
        return response.text



class AdzunaJobsSource(SourceConnector):
    """Fetch real job postings from the official Adzuna API when credentials are configured."""

    source_name = "adzuna_jobs"
    source_type = "job_posting"

    def fetch(self) -> list[RawRecord]:
        if not settings.adzuna_app_id or not settings.adzuna_app_key:
            return []

        country = settings.adzuna_country.strip().lower() or "us"
        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
        response = requests.get(
            url,
            params={
                "app_id": settings.adzuna_app_id,
                "app_key": settings.adzuna_app_key,
                "what": "data analyst data engineer data scientist",
                "results_per_page": settings.job_api_source_limit,
                "content-type": "application/json",
            },
            headers={"User-Agent": settings.user_agent},
            timeout=25,
        )
        response.raise_for_status()
        rows = response.json().get("results", [])[: settings.job_api_source_limit]
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
        rows = response.json().get("data", [])[: settings.job_api_source_limit]
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
        response = requests.get(
            self.url,
            params={"search": "data"},
            headers={"User-Agent": settings.user_agent},
            timeout=25,
        )
        response.raise_for_status()
        rows = response.json().get("jobs", [])[: settings.job_api_source_limit]
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

class CompositeJobSource(SourceConnector):
    source_name = "composite_job_sources"
    source_type = "job_posting"

    def __init__(self, sources: list[SourceConnector]) -> None:
        self.sources = sources

    def fetch(self) -> list[RawRecord]:
        records: list[RawRecord] = []
        for source in self.sources:
            try:
                records.extend(source.fetch())
            except requests.RequestException:
                continue
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


def parse_realpython_fake_jobs(html: str, base_url: str) -> list[ScrapedJobPosting]:
    soup = BeautifulSoup(html, "lxml")
    postings: list[ScrapedJobPosting] = []

    for card in soup.select(".card-content"):
        title = _text(card.select_one("h2.title"))
        company = _text(card.select_one("h3.company"))
        location = _text(card.select_one("p.location"))
        date = _text(card.select_one("time")) or None
        links = card.select("footer a")
        details_url = urljoin(base_url, links[-1].get("href", "")) if links else base_url

        if not title:
            continue

        postings.append(
            ScrapedJobPosting(
                title=title,
                company=company or "Unknown",
                location=location or "Unknown",
                description=" ".join(filter(None, [title, company, location])),
                posted_at=date,
                url=details_url,
            )
        )

    return postings


def parse_ycombinator_jobs(html: str, base_url: str) -> list[ScrapedJobPosting]:
    soup = BeautifulSoup(html, "lxml")
    postings: list[ScrapedJobPosting] = []

    for link in soup.select('a[href*="/companies/"][href*="/jobs/"]'):
        card = link.find_parent("li")
        if card is None:
            continue

        title = _text(link)
        card_text = _text(card)
        salary_min, salary_max = _salary_from_text(card_text)
        detail_text = _detail_line_from_yc_card(card_text, title)
        company = _company_from_yc_card(detail_text)
        location = _location_from_yc_detail(detail_text)
        description = " ".join(part for part in [title, company, detail_text] if part)

        if not title:
            continue

        postings.append(
            ScrapedJobPosting(
                title=title,
                company=company or "Y Combinator Company",
                location=location or "Unknown",
                description=description,
                posted_at=datetime.now(timezone.utc).date().isoformat(),
                url=urljoin(base_url, link.get("href", "")),
                salary_min=salary_min,
                salary_max=salary_max,
            )
        )

    return postings


def _company_from_yc_card(card_text: str) -> str:
    match = re.match(r"(.+?)\s+\([A-Z]\d{2}\)", card_text)
    if match:
        return match.group(1).strip()
    return _split_yc_detail_parts(card_text)[0] if card_text else ""


def _detail_line_from_yc_card(card_text: str, title: str) -> str:
    if title not in card_text:
        return card_text
    after_title = card_text.split(title, 1)[-1]
    return after_title.replace("Apply", "").strip()


def _salary_from_text(text: str) -> tuple[int | None, int | None]:
    match = re.search(r"\$(\d+)(K)?\s*-\s*\$(\d+)(K)?", text, flags=re.IGNORECASE)
    if not match:
        return None, None
    low = int(match.group(1)) * (1000 if match.group(2) else 1)
    high = int(match.group(3)) * (1000 if match.group(4) else 1)
    return low, high


def _location_from_yc_detail(detail_text: str) -> str:
    parts = _split_yc_detail_parts(detail_text)
    if not parts:
        return "Unknown"
    return parts[-1]


def _split_yc_detail_parts(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?:ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢|Ã¢â‚¬Â¢)", text) if part.strip()]



def html_to_text(value: object) -> str:
    if value is None:
        return ""
    return BeautifulSoup(str(value), "lxml").get_text(" ", strip=True)


def stable_text_id(*parts: object) -> str:
    key = "|".join(str(part or "") for part in parts).lower()
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


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

def stable_job_id(posting: ScrapedJobPosting) -> str:
    key = "|".join([posting.title, posting.company, posting.location, posting.url]).lower()
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def infer_remote_type(location: str, description: str) -> str:
    text = f"{location} {description}".lower()
    if re.search(r"\bremote\b", text):
        return "Remote"
    if re.search(r"\bhybrid\b", text):
        return "Hybrid"
    return "On-site"


def _text(node: object | None) -> str:
    if node is None:
        return ""
    return node.get_text(" ", strip=True)  # type: ignore[attr-defined]


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
