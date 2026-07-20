from __future__ import annotations

import pandas as pd

from src.ingestion.certification_sources import load_certification_catalog
from src.domain.technology import technology_skill_role_families


CERTIFICATION_RECOMMENDATIONS = [
    {
        "skill": "SQL",
        "certification_name": "HackerRank SQL Certificate",
        "provider": "HackerRank",
        "level": "Beginner",
        "free_or_paid": "Free",
        "estimated_cost_usd": 0,
        "target_roles": "Data Analyst | BI Analyst | Analytics Engineer",
        "url": "https://www.hackerrank.com/skills-verification/sql_basic",
        "priority_score": 82,
    },
    {
        "skill": "Tableau",
        "certification_name": "Tableau Desktop Specialist",
        "provider": "Tableau",
        "level": "Beginner",
        "free_or_paid": "Paid",
        "estimated_cost_usd": 100,
        "target_roles": "BI Analyst | Data Visualization Specialist",
        "url": "https://www.tableau.com/learn/certification/desktop-specialist",
        "priority_score": 72,
    },
    {
        "skill": "dbt",
        "certification_name": "dbt Analytics Engineering Certification",
        "provider": "dbt Labs",
        "level": "Intermediate",
        "free_or_paid": "Paid",
        "estimated_cost_usd": 200,
        "target_roles": "Analytics Engineer | Data Engineer",
        "url": "https://www.getdbt.com/certifications/analytics-engineering",
        "priority_score": 86,
    },
    {
        "skill": "Snowflake",
        "certification_name": "SnowPro Core Certification",
        "provider": "Snowflake",
        "level": "Intermediate",
        "free_or_paid": "Paid",
        "estimated_cost_usd": 175,
        "target_roles": "Data Engineer | Warehouse Engineer",
        "url": "https://www.snowflake.com/en/data-cloud-academy/certifications/",
        "priority_score": 80,
    },
    {
        "skill": "Databricks",
        "certification_name": "Databricks Certified Data Engineer Associate",
        "provider": "Databricks",
        "level": "Intermediate",
        "free_or_paid": "Paid",
        "estimated_cost_usd": 200,
        "target_roles": "Data Engineer | Lakehouse Engineer",
        "url": "https://www.databricks.com/learn/certification/data-engineer-associate",
        "priority_score": 82,
    },
]


def build_certification_recommendations(skill_gap_df: pd.DataFrame) -> pd.DataFrame:
    certs = pd.DataFrame([*CERTIFICATION_RECOMMENDATIONS, *load_certification_catalog()])
    certs["source_name"] = certs.get("source_name", "curated_certification_catalog").fillna(
        "curated_certification_catalog"
    )
    certs["source_confidence"] = certs.get("source_confidence", "curated_demo").fillna("curated_demo")
    certs["last_verified"] = certs.get("last_verified", "2026-07-20").fillna("2026-07-20")
    certs["role_families"] = certs["skill"].map(_cert_role_families)
    certs = certs.drop_duplicates(subset=["skill", "certification_name"], keep="last")
    if skill_gap_df.empty or "skill" not in skill_gap_df:
        return certs

    cols = ["skill", "opportunity_index", "opportunity_label", "job_demand", "target_job_roles"]
    enrich = skill_gap_df[[col for col in cols if col in skill_gap_df]].copy()
    out = certs.merge(enrich, on="skill", how="left", suffixes=("", "_market"))
    out["market_priority"] = pd.to_numeric(out.get("opportunity_index"), errors="coerce").fillna(0)
    out["recommendation_score"] = (
        (pd.to_numeric(out["priority_score"], errors="coerce").fillna(0) * 0.55)
        + (out["market_priority"] * 0.45)
    ).round().astype(int)
    return out.sort_values(["recommendation_score", "priority_score"], ascending=[False, False])


def _cert_role_families(skill: object) -> str:
    name = str(skill or "")
    technology_families = technology_skill_role_families(name)
    if technology_families:
        return "|".join(technology_families)
    legacy = {
        "SQL": "Data & Analytics|Database",
        "Python": "Data & Analytics|AI & Machine Learning|Software Engineering",
        "Power BI": "Data & Analytics",
        "Microsoft Fabric": "Data & Analytics|Cloud & Platform",
        "Data Pipelines": "Data & Analytics|Cloud & Platform",
        "Data Visualization": "Data & Analytics",
        "Machine Learning": "AI & Machine Learning",
        "AWS": "Cloud & Platform",
        "Azure": "Cloud & Platform",
        "GCP": "Cloud & Platform",
    }
    return legacy.get(name, "Other Technology")
