from __future__ import annotations

from typing import Any

import requests

from src.config.settings import settings
from src.ingestion.base import RawRecord, SourceConnector, utc_now


DATA_ROLE_KEYWORDS = {
    "data-analyst",
    "data-engineer",
    "data-scientist",
    "ai-engineer",
}

DATA_SUBJECT_KEYWORDS = {
    "data-analysis",
    "data-engineering",
    "data-science",
    "machine-learning",
    "artificial-intelligence",
    "databases",
    "analytics",
    "visualization",
}

DATA_TEXT_KEYWORDS = {
    "analytics",
    "data analysis",
    "data analytics",
    "data engineering",
    "data science",
    "database",
    "machine learning",
    "python",
    "sql",
    "power bi",
    "fabric",
    "azure synapse",
    "spark",
}


YOUTUBE_FALLBACK_CATALOG = [
    {
        "external_id": "youtube-python-data-engineering",
        "title": "Python Data Engineering Tutorial",
        "platform": "YouTube Learning",
        "level": "Beginner",
        "rating": None,
        "duration_minutes": None,
        "description": "Video tutorial covering Python, APIs, ETL, pandas, SQL, PostgreSQL, and data pipelines.",
        "subjects": "python|etl|apis|data-engineering|sql",
        "roles": "data-engineer|data-analyst",
        "products": "python|postgresql|pandas",
        "last_modified": "2026-06-01",
        "url": "https://www.youtube.com/results?search_query=python+data+engineering+tutorial",
    },
    {
        "external_id": "youtube-power-bi-dashboard",
        "title": "Power BI Full Course for Data Analysts",
        "platform": "YouTube Learning",
        "level": "Beginner",
        "rating": None,
        "duration_minutes": None,
        "description": "Video course covering Power BI, DAX, dashboards, KPI reporting, data visualization, and analytics.",
        "subjects": "power-bi|data-visualization|dashboarding|analytics",
        "roles": "data-analyst|bi-analyst",
        "products": "power-bi",
        "last_modified": "2026-06-01",
        "url": "https://www.youtube.com/results?search_query=power+bi+full+course+data+analyst",
    },
    {
        "external_id": "youtube-sql-analytics",
        "title": "SQL for Data Analytics Course",
        "platform": "YouTube Learning",
        "level": "Beginner",
        "rating": None,
        "duration_minutes": None,
        "description": "Video course covering SQL, joins, window functions, data modeling, analytics, and interview practice.",
        "subjects": "sql|analytics|data-modeling",
        "roles": "data-analyst|analytics-engineer",
        "products": "sql|postgresql",
        "last_modified": "2026-06-01",
        "url": "https://www.youtube.com/results?search_query=sql+for+data+analytics+course",
    },
    {
        "external_id": "youtube-airflow-dbt",
        "title": "Airflow and dbt Data Pipeline Tutorial",
        "platform": "YouTube Learning",
        "level": "Intermediate",
        "rating": None,
        "duration_minutes": None,
        "description": "Video tutorial covering Airflow, dbt, Docker, orchestration, ELT, data quality, and analytics engineering.",
        "subjects": "airflow|dbt|docker|elt|data-quality",
        "roles": "data-engineer|analytics-engineer",
        "products": "airflow|dbt|docker",
        "last_modified": "2026-06-01",
        "url": "https://www.youtube.com/results?search_query=airflow+dbt+data+pipeline+tutorial",
    },
]


OPEN_COURSE_CATALOG = [
    {
        "external_id": "open-course-python-data-analysis",
        "title": "Python for Data Analysis",
        "platform": "Open Course Catalog",
        "level": "Beginner",
        "rating": None,
        "duration_minutes": 480,
        "description": "Learn Python, pandas, NumPy, visualization, APIs, and data cleaning for analytics projects.",
        "subjects": "python|data-analysis|pandas|numpy|apis",
        "roles": "data-analyst|data-scientist",
        "products": "python|pandas",
        "last_modified": "2026-01-15",
        "url": "https://www.freecodecamp.org/learn/data-analysis-with-python/",
    },
    {
        "external_id": "open-course-sql-analytics",
        "title": "SQL Analytics and Databases",
        "platform": "Open Course Catalog",
        "level": "Beginner",
        "rating": None,
        "duration_minutes": 360,
        "description": "Practice SQL, joins, aggregations, PostgreSQL, data modeling, and analytics-ready query patterns.",
        "subjects": "sql|databases|data-modeling|analytics",
        "roles": "data-analyst|data-engineer|analytics-engineer",
        "products": "postgresql|sql",
        "last_modified": "2026-02-10",
        "url": "https://www.kaggle.com/learn/intro-to-sql",
    },
    {
        "external_id": "open-course-bi-dashboarding",
        "title": "Business Intelligence Dashboarding",
        "platform": "Open Course Catalog",
        "level": "Intermediate",
        "rating": None,
        "duration_minutes": 300,
        "description": "Design KPI dashboards with Power BI, Tableau, data visualization, DAX-style measures, and storytelling.",
        "subjects": "business-intelligence|data-visualization|dashboards",
        "roles": "data-analyst|bi-analyst|bi-developer",
        "products": "power-bi|tableau",
        "last_modified": "2026-03-05",
        "url": "https://learn.microsoft.com/training/powerplatform/power-bi",
    },
    {
        "external_id": "open-course-modern-data-engineering",
        "title": "Modern Data Engineering Foundations",
        "platform": "Open Course Catalog",
        "level": "Intermediate",
        "rating": None,
        "duration_minutes": 540,
        "description": "Build ETL and ELT pipelines with Airflow, dbt, Docker, APIs, data quality checks, and cloud warehouses.",
        "subjects": "data-engineering|etl|elt|data-quality|orchestration",
        "roles": "data-engineer|analytics-engineer",
        "products": "airflow|dbt|docker",
        "last_modified": "2026-04-12",
        "url": "https://airflow.apache.org/docs/apache-airflow/stable/tutorial/index.html",
    },
    {
        "external_id": "open-course-cloud-data-platforms",
        "title": "Cloud Data Platforms",
        "platform": "Open Course Catalog",
        "level": "Intermediate",
        "rating": None,
        "duration_minutes": 420,
        "description": "Compare AWS, Azure, GCP, Snowflake, Databricks, Spark, and lakehouse patterns for data platforms.",
        "subjects": "cloud|data-engineering|big-data|lakehouse",
        "roles": "cloud-data-engineer|data-platform-engineer",
        "products": "aws|azure|gcp|snowflake|databricks|spark",
        "last_modified": "2026-05-20",
        "url": "https://www.databricks.com/learn/training/home",
    },
    {
        "external_id": "open-course-genai-analytics",
        "title": "Generative AI for Data Workflows",
        "platform": "Open Course Catalog",
        "level": "Intermediate",
        "rating": None,
        "duration_minutes": 360,
        "description": "Apply GenAI, LLMs, NLP, responsible AI, and APIs to analytics automation and data products.",
        "subjects": "generative-ai|machine-learning|nlp|responsible-ai",
        "roles": "data-scientist|ai-engineer|analytics-engineer",
        "products": "llms|apis",
        "last_modified": "2026-06-01",
        "url": "https://www.deeplearning.ai/short-courses/",
    },
]


VENDOR_DOCS_CATALOG = [
    {
        "external_id": "vendor-docs-airflow-orchestration",
        "title": "Apache Airflow Orchestration Tutorial",
        "platform": "Vendor Docs Catalog",
        "level": "Intermediate",
        "rating": None,
        "duration_minutes": 240,
        "description": "Learn Airflow DAGs, data pipelines, scheduling, retries, orchestration, and data engineering operations.",
        "subjects": "airflow|data-engineering|orchestration|data-pipelines",
        "roles": "data-engineer|analytics-engineer",
        "products": "airflow",
        "last_modified": "2026-03-15",
        "url": "https://airflow.apache.org/docs/apache-airflow/stable/tutorial/index.html",
    },
    {
        "external_id": "vendor-docs-dbt-fundamentals",
        "title": "dbt Fundamentals",
        "platform": "Vendor Docs Catalog",
        "level": "Intermediate",
        "rating": None,
        "duration_minutes": 300,
        "description": "Build dbt models, tests, documentation, SQL transformations, semantic layers, and analytics engineering workflows.",
        "subjects": "dbt|sql|analytics-engineering|data-quality",
        "roles": "analytics-engineer|data-engineer",
        "products": "dbt",
        "last_modified": "2026-04-18",
        "url": "https://docs.getdbt.com/guides",
    },
    {
        "external_id": "vendor-docs-snowflake-lakehouse",
        "title": "Snowflake Data Engineering Guides",
        "platform": "Vendor Docs Catalog",
        "level": "Intermediate",
        "rating": None,
        "duration_minutes": 360,
        "description": "Use Snowflake, SQL, data modeling, ELT, data quality, and warehouse optimization for analytics-ready data.",
        "subjects": "snowflake|sql|elt|data-modeling",
        "roles": "data-engineer|analytics-engineer",
        "products": "snowflake",
        "last_modified": "2026-05-08",
        "url": "https://docs.snowflake.com/en/guides",
    },
]


UNIVERSITY_OPEN_CATALOG = [
    {
        "external_id": "university-open-statistics",
        "title": "Statistics and Inference for Data Science",
        "platform": "University Open Catalog",
        "level": "Beginner",
        "rating": None,
        "duration_minutes": 600,
        "description": "Study statistics, forecasting, experimentation, A/B testing, regression, and uncertainty for data science decisions.",
        "subjects": "statistics|forecasting|experimentation|data-science",
        "roles": "data-scientist|data-analyst|product-analyst",
        "products": "statistics",
        "last_modified": "2026-01-30",
        "url": "https://www.edx.org/learn/statistics",
    },
    {
        "external_id": "university-open-ml",
        "title": "Machine Learning Foundations",
        "platform": "University Open Catalog",
        "level": "Intermediate",
        "rating": None,
        "duration_minutes": 720,
        "description": "Learn machine learning, Python, scikit-learn, PyTorch, NLP, model evaluation, and responsible AI concepts.",
        "subjects": "machine-learning|python|nlp|responsible-ai",
        "roles": "data-scientist|ml-engineer|ai-engineer",
        "products": "python|scikit-learn|pytorch",
        "last_modified": "2026-02-28",
        "url": "https://ocw.mit.edu/search/?q=machine%20learning",
    },
    {
        "external_id": "university-open-data-visualization",
        "title": "Data Visualization and Storytelling",
        "platform": "University Open Catalog",
        "level": "Beginner",
        "rating": None,
        "duration_minutes": 420,
        "description": "Design data visualization, dashboards, Tableau, Power BI, charts, and executive communication for analytics users.",
        "subjects": "data-visualization|business-intelligence|analytics",
        "roles": "data-analyst|bi-analyst",
        "products": "tableau|power-bi",
        "last_modified": "2026-03-22",
        "url": "https://www.coursera.org/browse/data-science/data-analysis",
    },
]


class OpenCourseCatalogSource(SourceConnector):
    """Open learning resources used for repeatable local runs."""

    source_name = "open_course_catalog"
    source_type = "course_listing"

    def fetch(self) -> list[RawRecord]:
        collected_at = utc_now()
        return [
            RawRecord(
                source_name=self.source_name,
                source_type=self.source_type,
                source_url=item["url"],
                collected_at=collected_at,
                payload=item,
            )
            for item in OPEN_COURSE_CATALOG
        ]


class VendorDocsCourseSource(SourceConnector):
    """Curated vendor documentation and training resources for data tools."""

    source_name = "vendor_docs_catalog"
    source_type = "course_listing"

    def fetch(self) -> list[RawRecord]:
        collected_at = utc_now()
        return [
            RawRecord(
                source_name=self.source_name,
                source_type=self.source_type,
                source_url=item["url"],
                collected_at=collected_at,
                payload=item,
            )
            for item in VENDOR_DOCS_CATALOG
        ]


class UniversityOpenCourseSource(SourceConnector):
    """Curated university/open learning resources for analytical foundations."""

    source_name = "university_open_catalog"
    source_type = "course_listing"

    def fetch(self) -> list[RawRecord]:
        collected_at = utc_now()
        return [
            RawRecord(
                source_name=self.source_name,
                source_type=self.source_type,
                source_url=item["url"],
                collected_at=collected_at,
                payload=item,
            )
            for item in UNIVERSITY_OPEN_CATALOG
        ]


class YouTubeLearningSource(SourceConnector):
    """Use the YouTube API when configured; otherwise use local fallback rows."""

    source_name = "youtube_learning"
    source_type = "course_listing"
    api_url = "https://www.googleapis.com/youtube/v3/search"

    def fetch(self) -> list[RawRecord]:
        collected_at = utc_now()
        items = self._fetch_from_api() if settings.youtube_api_key else YOUTUBE_FALLBACK_CATALOG
        return [
            RawRecord(
                source_name=self.source_name,
                source_type=self.source_type,
                source_url=item["url"],
                collected_at=collected_at,
                payload=item,
            )
            for item in items
        ]

    def _fetch_from_api(self) -> list[dict[str, Any]]:
        queries = [
            "python data engineering tutorial",
            "sql for data analytics course",
            "power bi data analyst full course",
            "airflow dbt data pipeline tutorial",
            "machine learning for data science course",
        ]
        rows: list[dict[str, Any]] = []
        per_query = max(1, settings.youtube_source_limit // len(queries))
        for query in queries:
            response = requests.get(
                self.api_url,
                params={
                    "part": "snippet",
                    "q": query,
                    "type": "video",
                    "maxResults": per_query,
                    "key": settings.youtube_api_key,
                },
                headers={"User-Agent": settings.user_agent},
                timeout=30,
            )
            response.raise_for_status()
            for item in response.json().get("items", []):
                video_id = item.get("id", {}).get("videoId")
                snippet = item.get("snippet", {})
                if not video_id:
                    continue
                title = snippet.get("title")
                description = snippet.get("description")
                rows.append(
                    {
                        "external_id": f"youtube-{video_id}",
                        "title": title,
                        "platform": "YouTube Learning",
                        "level": "Video",
                        "rating": None,
                        "duration_minutes": None,
                        "description": f"{title}. {description}",
                        "subjects": query.replace(" ", "|"),
                        "roles": "data-analyst|data-engineer|data-scientist",
                        "products": "",
                        "last_modified": snippet.get("publishedAt"),
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                    }
                )
        return rows or YOUTUBE_FALLBACK_CATALOG


class CompositeCourseSource(SourceConnector):
    source_name = "composite_course_sources"
    source_type = "course_listing"

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


class MicrosoftLearnCourseSource(SourceConnector):
    """Ingest module listings from the public Microsoft Learn catalog API."""

    source_name = "microsoft_learn_catalog"
    source_type = "course_listing"

    def __init__(self, url: str | None = None, limit: int | None = None) -> None:
        self.url = url or settings.course_source_url
        self.limit = limit or settings.course_source_limit

    def fetch(self) -> list[RawRecord]:
        modules = self._fetch_modules()
        relevant = [module for module in modules if is_relevant_module(module)]
        selected = relevant[: self.limit]
        collected_at = utc_now()

        return [
            RawRecord(
                source_name=self.source_name,
                source_type=self.source_type,
                source_url=module.get("url") or self.url,
                collected_at=collected_at,
                payload=normalize_microsoft_module(module),
            )
            for module in selected
        ]

    def _fetch_modules(self) -> list[dict[str, Any]]:
        response = requests.get(
            self.url,
            headers={"User-Agent": settings.user_agent},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        modules = data.get("modules", [])
        if not isinstance(modules, list):
            raise ValueError("Microsoft Learn catalog response did not include a modules list.")
        return [module for module in modules if isinstance(module, dict)]


def normalize_microsoft_module(module: dict[str, Any]) -> dict[str, Any]:
    levels = module.get("levels") or []
    subjects = module.get("subjects") or []
    roles = module.get("roles") or []
    products = module.get("products") or []

    return {
        "external_id": module.get("uid"),
        "title": module.get("title"),
        "platform": "Microsoft Learn",
        "level": ", ".join(levels) if isinstance(levels, list) else levels,
        "rating": None,
        "duration_minutes": module.get("duration_in_minutes"),
        "description": module.get("summary"),
        "subjects": "|".join(subjects) if isinstance(subjects, list) else subjects,
        "roles": "|".join(roles) if isinstance(roles, list) else roles,
        "products": "|".join(products) if isinstance(products, list) else products,
        "last_modified": module.get("last_modified"),
        "url": module.get("url"),
    }


def is_relevant_module(module: dict[str, Any]) -> bool:
    roles = set(_lower_list(module.get("roles")))
    subjects = set(_lower_list(module.get("subjects")))
    products = set(_lower_list(module.get("products")))
    text = " ".join(
        [
            str(module.get("title") or ""),
            str(module.get("summary") or ""),
            " ".join(products),
        ]
    ).lower()

    role_match = bool(roles & DATA_ROLE_KEYWORDS)
    strong_subject_match = bool(
        subjects
        & {
            "data-analysis",
            "data-science",
            "machine-learning",
            "artificial-intelligence",
            "databases",
            "analytics",
            "visualization",
        }
    )
    broad_subject_match = bool(subjects & {"data-engineering"})
    text_match = any(keyword in text for keyword in DATA_TEXT_KEYWORDS)
    product_match = any(
        product in products
        for product in {
            "azure-machine-learning",
            "azure-sql-database",
            "azure-databricks",
            "azure-synapse-analytics",
            "power-bi",
            "fabric",
            "microsoft-fabric",
        }
    )

    role_with_data_signal = role_match and (strong_subject_match or broad_subject_match or product_match or text_match)
    return strong_subject_match or product_match or (broad_subject_match and text_match) or text_match or role_with_data_signal


def _lower_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip().lower() for item in value if str(item).strip()]
    if value:
        return [str(value).strip().lower()]
    return []
