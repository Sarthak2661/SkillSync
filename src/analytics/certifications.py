from __future__ import annotations

import pandas as pd


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
        "skill": "Power BI",
        "certification_name": "Microsoft PL-300 Power BI Data Analyst",
        "provider": "Microsoft",
        "level": "Intermediate",
        "free_or_paid": "Paid",
        "estimated_cost_usd": 165,
        "target_roles": "Data Analyst | BI Developer | Reporting Analyst",
        "url": "https://learn.microsoft.com/credentials/certifications/power-bi-data-analyst-associate/",
        "priority_score": 88,
    },
    {
        "skill": "Azure Data Factory",
        "certification_name": "Microsoft DP-203 Azure Data Engineer",
        "provider": "Microsoft",
        "level": "Intermediate",
        "free_or_paid": "Paid",
        "estimated_cost_usd": 165,
        "target_roles": "Azure Data Engineer | Cloud Data Engineer",
        "url": "https://learn.microsoft.com/credentials/certifications/azure-data-engineer/",
        "priority_score": 84,
    },
    {
        "skill": "AWS",
        "certification_name": "AWS Certified Data Engineer - Associate",
        "provider": "AWS",
        "level": "Intermediate",
        "free_or_paid": "Paid",
        "estimated_cost_usd": 150,
        "target_roles": "Cloud Data Engineer | Data Platform Engineer",
        "url": "https://aws.amazon.com/certification/certified-data-engineer-associate/",
        "priority_score": 84,
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
        "skill": "Python",
        "certification_name": "freeCodeCamp Data Analysis with Python",
        "provider": "freeCodeCamp",
        "level": "Beginner",
        "free_or_paid": "Free",
        "estimated_cost_usd": 0,
        "target_roles": "Data Analyst | Data Scientist | Data Engineer",
        "url": "https://www.freecodecamp.org/learn/data-analysis-with-python/",
        "priority_score": 78,
    },
    {
        "skill": "Machine Learning",
        "certification_name": "Google Professional Machine Learning Engineer",
        "provider": "Google Cloud",
        "level": "Advanced",
        "free_or_paid": "Paid",
        "estimated_cost_usd": 200,
        "target_roles": "ML Engineer | Data Scientist",
        "url": "https://cloud.google.com/learn/certification/machine-learning-engineer",
        "priority_score": 76,
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
    certs = pd.DataFrame(CERTIFICATION_RECOMMENDATIONS)
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
