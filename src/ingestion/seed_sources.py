from __future__ import annotations

from src.ingestion.base import RawRecord, SourceConnector, utc_now


class SeedJobPostingSource(SourceConnector):
    source_name = "seed_job_postings"
    source_type = "job_posting"

    def fetch(self) -> list[RawRecord]:
        collected_at = utc_now()
        records = [
            {
                "external_id": "job-001",
                "title": "Data Engineer",
                "company": "Northstar Analytics",
                "location": "New York, NY",
                "remote_type": "Hybrid",
                "salary_min": 110000,
                "salary_max": 145000,
                "description": "Build Python and SQL pipelines with Airflow, dbt, PostgreSQL, and AWS.",
                "posted_at": "2026-06-20",
                "url": "https://example.com/jobs/data-engineer-001",
            },
            {
                "external_id": "job-002",
                "title": "Data Analyst",
                "company": "BrightCart",
                "location": "Remote",
                "remote_type": "Remote",
                "salary_min": 78000,
                "salary_max": 98000,
                "description": "Analyze ecommerce KPIs with SQL, Python, Power BI, Excel, and A/B testing.",
                "posted_at": "2026-06-18",
                "url": "https://example.com/jobs/data-analyst-002",
            },
            {
                "external_id": "job-003",
                "title": "Data Scientist",
                "company": "CareMap AI",
                "location": "Boston, MA",
                "remote_type": "On-site",
                "salary_min": 125000,
                "salary_max": 165000,
                "description": "Train machine learning models using Python, pandas, scikit-learn, NLP, and cloud data platforms.",
                "posted_at": "2026-06-16",
                "url": "https://example.com/jobs/data-scientist-003",
            },
        ]
        return [
            RawRecord(
                source_name=self.source_name,
                source_type=self.source_type,
                source_url=item["url"],
                collected_at=collected_at,
                payload=item,
            )
            for item in records
        ]


class SeedCourseListingSource(SourceConnector):
    source_name = "seed_course_listings"
    source_type = "course_listing"

    def fetch(self) -> list[RawRecord]:
        collected_at = utc_now()
        records = [
            {
                "external_id": "course-001",
                "title": "SQL for Data Analytics",
                "platform": "Open Learning Catalog",
                "level": "Beginner",
                "rating": 4.7,
                "description": "Learn SQL joins, aggregations, window functions, dashboards, and analytics workflows.",
                "url": "https://example.com/courses/sql-analytics",
            },
            {
                "external_id": "course-002",
                "title": "Modern Data Engineering with Python",
                "platform": "Open Learning Catalog",
                "level": "Intermediate",
                "rating": 4.6,
                "description": "Build ETL pipelines with Python, pandas, PostgreSQL, Airflow, APIs, and data quality checks.",
                "url": "https://example.com/courses/python-data-engineering",
            },
            {
                "external_id": "course-003",
                "title": "Power BI Dashboard Design",
                "platform": "Open Learning Catalog",
                "level": "Beginner",
                "rating": 4.5,
                "description": "Create Power BI reports, DAX measures, KPI cards, and executive dashboards.",
                "url": "https://example.com/courses/power-bi-dashboard-design",
            },
        ]
        return [
            RawRecord(
                source_name=self.source_name,
                source_type=self.source_type,
                source_url=item["url"],
                collected_at=collected_at,
                payload=item,
            )
            for item in records
        ]
