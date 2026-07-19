from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from src.ingestion.base import RawRecord
from src.analytics.onet_reference import onet_growth_score, onet_profile_for_skill, onet_salary_score
from src.analytics.source_confidence import confidence_for_source


@dataclass(frozen=True)
class SkillDefinition:
    skill: str
    category: str
    patterns: tuple[str, ...]


@dataclass(frozen=True)
class SkillMatch:
    skill: str
    category: str
    matched_terms: tuple[str, ...]
    confidence: float


@dataclass(frozen=True)
class SkillMarketSignal:
    growth_score: int
    salary_premium_score: int
    saturation_score: int
    market_direction: str


SKILL_DEFINITIONS: tuple[SkillDefinition, ...] = (
    SkillDefinition("Python", "Programming", (r"\bpython\b",)),
    SkillDefinition("R", "Programming", (r"\br programming\b", r"\br language\b")),
    SkillDefinition("SQL", "Database", (r"\bsql\b", r"\bt\s*sql\b", r"\btransact\s*sql\b")),
    SkillDefinition("PostgreSQL", "Database", (r"\bpostgresql\b", r"\bpostgres\b")),
    SkillDefinition("MySQL", "Database", (r"\bmysql\b",)),
    SkillDefinition("SQL Server", "Database", (r"\bsql server\b", r"\bmssql\b")),
    SkillDefinition("NoSQL", "Database", (r"\bnosql\b", r"\bcosmos db\b", r"\bmongodb\b")),
    SkillDefinition("Data Modeling", "Data Engineering", (r"\bdata model(?:ing|ling)?\b", r"\bschema design\b")),
    SkillDefinition("ETL", "Data Engineering", (r"\betl\b", r"\bextract[, ]+transform[, ]+load\b")),
    SkillDefinition("ELT", "Data Engineering", (r"\belt\b",)),
    SkillDefinition("Data Pipelines", "Data Engineering", (r"\bdata pipeline[s]?\b", r"\bpipeline orchestration\b")),
    SkillDefinition("Airflow", "Data Engineering", (r"\bairflow\b", r"\bapache airflow\b")),
    SkillDefinition("dbt", "Data Engineering", (r"\bdbt\b",)),
    SkillDefinition("Spark", "Data Engineering", (r"\bspark\b", r"\bapache spark\b", r"\bpyspark\b")),
    SkillDefinition("Databricks", "Data Engineering", (r"\bdatabricks\b",)),
    SkillDefinition("Snowflake", "Data Engineering", (r"\bsnowflake\b",)),
    SkillDefinition("Azure Data Factory", "Data Engineering", (r"\bazure data factory\b", r"\badf\b")),
    SkillDefinition("Microsoft Fabric", "Analytics Platform", (r"\bmicrosoft fabric\b", r"\bfabric\b")),
    SkillDefinition("AWS", "Cloud", (r"\baws\b", r"\bamazon web services\b")),
    SkillDefinition("Azure", "Cloud", (r"\bazure\b",)),
    SkillDefinition("GCP", "Cloud", (r"\bgcp\b", r"\bgoogle cloud\b")),
    SkillDefinition("Power BI", "BI & Visualization", (r"\bpower\s*bi\b", r"\bdax\b")),
    SkillDefinition("Tableau", "BI & Visualization", (r"\btableau\b",)),
    SkillDefinition("Excel", "BI & Visualization", (r"\bexcel\b", r"\bpivot table[s]?\b")),
    SkillDefinition("Data Visualization", "BI & Visualization", (r"\bdata visuali[sz]ation\b", r"\bdashboard[s]?\b")),
    SkillDefinition("Machine Learning", "Machine Learning", (r"\bmachine learning\b", r"\bml\b")),
    SkillDefinition("Deep Learning", "Machine Learning", (r"\bdeep learning\b", r"\bneural network[s]?\b")),
    SkillDefinition("NLP", "Machine Learning", (r"\bnlp\b", r"\bnatural language processing\b")),
    SkillDefinition("GenAI", "Machine Learning", (r"\bgenai\b", r"\bgenerative ai\b", r"\bgenerative artificial intelligence\b")),
    SkillDefinition("LLMs", "Machine Learning", (r"\bllm[s]?\b", r"\blarge language model[s]?\b")),
    SkillDefinition("scikit-learn", "Machine Learning", (r"\bscikit\s*learn\b", r"\bsklearn\b")),
    SkillDefinition("TensorFlow", "Machine Learning", (r"\btensorflow\b",)),
    SkillDefinition("PyTorch", "Machine Learning", (r"\bpytorch\b",)),
    SkillDefinition("pandas", "Python Data Stack", (r"\bpandas\b", r"\bdataframe[s]?\b")),
    SkillDefinition("NumPy", "Python Data Stack", (r"\bnumpy\b",)),
    SkillDefinition("Matplotlib", "Python Data Stack", (r"\bmatplotlib\b",)),
    SkillDefinition("Seaborn", "Python Data Stack", (r"\bseaborn\b",)),
    SkillDefinition("Statistics", "Analysis", (r"\bstatistics\b", r"\bstatistical\b")),
    SkillDefinition("A/B Testing", "Analysis", (r"\ba\s*b testing\b", r"\bab testing\b", r"\bexperimentation\b")),
    SkillDefinition("Forecasting", "Analysis", (r"\bforecast(?:ing)?\b", r"\btime series\b")),
    SkillDefinition("APIs", "Software Engineering", (r"\bapi\b", r"\bapis\b", r"\brest\b")),
    SkillDefinition("Docker", "Software Engineering", (r"\bdocker\b", r"\bcontaineri[sz]e\b")),
    SkillDefinition("Git", "Software Engineering", (r"\bgit\b", r"\bgithub\b")),
    SkillDefinition("FastAPI", "Software Engineering", (r"\bfastapi\b",)),
    SkillDefinition("Data Quality", "Data Governance", (r"\bdata quality\b", r"\bvalidation checks?\b")),
    SkillDefinition("Responsible AI", "Data Governance", (r"\bresponsible ai\b", r"\bmodel governance\b")),
)


SKILL_PATTERNS: dict[str, list[str]] = {
    definition.skill: list(definition.patterns) for definition in SKILL_DEFINITIONS
}


DEFAULT_MARKET_SIGNAL = SkillMarketSignal(
    growth_score=50,
    salary_premium_score=50,
    saturation_score=50,
    market_direction="Stable",
)


SKILL_MARKET_SIGNALS: dict[str, SkillMarketSignal] = {
    "Python": SkillMarketSignal(65, 65, 60, "Growing"),
    "R": SkillMarketSignal(45, 50, 55, "Stable"),
    "SQL": SkillMarketSignal(55, 55, 70, "Stable"),
    "PostgreSQL": SkillMarketSignal(60, 60, 45, "Growing"),
    "MySQL": SkillMarketSignal(40, 45, 60, "Stable"),
    "SQL Server": SkillMarketSignal(45, 50, 55, "Stable"),
    "NoSQL": SkillMarketSignal(55, 60, 45, "Growing"),
    "Data Modeling": SkillMarketSignal(60, 65, 45, "Growing"),
    "ETL": SkillMarketSignal(55, 60, 55, "Stable"),
    "ELT": SkillMarketSignal(65, 65, 35, "Growing"),
    "Data Pipelines": SkillMarketSignal(65, 65, 45, "Growing"),
    "Airflow": SkillMarketSignal(75, 75, 35, "Growing"),
    "dbt": SkillMarketSignal(80, 75, 30, "Growing"),
    "Spark": SkillMarketSignal(55, 70, 50, "Stable"),
    "Databricks": SkillMarketSignal(70, 75, 35, "Growing"),
    "Snowflake": SkillMarketSignal(65, 70, 40, "Growing"),
    "Azure Data Factory": SkillMarketSignal(65, 65, 45, "Growing"),
    "Microsoft Fabric": SkillMarketSignal(80, 70, 25, "Growing"),
    "AWS": SkillMarketSignal(65, 70, 60, "Growing"),
    "Azure": SkillMarketSignal(65, 65, 55, "Growing"),
    "GCP": SkillMarketSignal(60, 70, 45, "Growing"),
    "Power BI": SkillMarketSignal(60, 55, 65, "Stable"),
    "Tableau": SkillMarketSignal(45, 50, 65, "Stable"),
    "Excel": SkillMarketSignal(35, 35, 85, "Basic requirement"),
    "Data Visualization": SkillMarketSignal(55, 50, 65, "Stable"),
    "Machine Learning": SkillMarketSignal(65, 75, 60, "Growing"),
    "Deep Learning": SkillMarketSignal(55, 75, 50, "Specialized"),
    "NLP": SkillMarketSignal(70, 75, 40, "Growing"),
    "GenAI": SkillMarketSignal(90, 80, 30, "Growing"),
    "LLMs": SkillMarketSignal(90, 80, 30, "Growing"),
    "scikit-learn": SkillMarketSignal(55, 60, 55, "Stable"),
    "TensorFlow": SkillMarketSignal(45, 65, 60, "Stable"),
    "PyTorch": SkillMarketSignal(60, 70, 50, "Growing"),
    "pandas": SkillMarketSignal(55, 55, 70, "Basic requirement"),
    "NumPy": SkillMarketSignal(45, 50, 65, "Basic requirement"),
    "Matplotlib": SkillMarketSignal(35, 40, 65, "Stable"),
    "Seaborn": SkillMarketSignal(35, 40, 60, "Stable"),
    "Statistics": SkillMarketSignal(50, 55, 65, "Stable"),
    "A/B Testing": SkillMarketSignal(55, 65, 50, "Stable"),
    "Forecasting": SkillMarketSignal(60, 65, 45, "Growing"),
    "APIs": SkillMarketSignal(60, 60, 55, "Growing"),
    "Docker": SkillMarketSignal(60, 60, 55, "Growing"),
    "Git": SkillMarketSignal(40, 40, 80, "Basic requirement"),
    "FastAPI": SkillMarketSignal(65, 60, 35, "Growing"),
    "Data Quality": SkillMarketSignal(70, 65, 35, "Growing"),
    "Responsible AI": SkillMarketSignal(80, 75, 25, "Growing"),
}


def extract_skills(text: str) -> list[str]:
    return [match.skill for match in extract_skill_matches(text)]


def extract_skill_matches(text: str) -> list[SkillMatch]:
    normalized = normalize_skill_text(text)
    matches: list[SkillMatch] = []

    for definition in SKILL_DEFINITIONS:
        matched_terms = tuple(
            sorted(
                {
                    match.group(0).strip()
                    for pattern in definition.patterns
                    for match in re.finditer(pattern, normalized, flags=re.IGNORECASE)
                }
            )
        )
        if matched_terms:
            confidence = min(1.0, 0.65 + (0.1 * len(matched_terms)))
            matches.append(
                SkillMatch(
                    skill=definition.skill,
                    category=definition.category,
                    matched_terms=matched_terms,
                    confidence=round(confidence, 2),
                )
            )

    return sorted(matches, key=lambda match: match.skill.lower())


def normalize_skill_text(text: str) -> str:
    text = text.replace("&", " and ")
    text = re.sub(r"[/_+-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def normalize_job_postings(records: Iterable[RawRecord]) -> pd.DataFrame:
    rows = []
    for record in records:
        item = record.payload
        text = build_skill_text(
            item,
            ["title", "description", "company", "location", "remote_type"],
        )
        skill_matches = extract_skill_matches(text)
        rows.append(
            {
                "source_name": record.source_name,
                "source_confidence": confidence_for_source(record.source_name),
                "external_id": item.get("external_id"),
                "title": item.get("title"),
                "company": item.get("company"),
                "location": item.get("location"),
                "remote_type": item.get("remote_type"),
                "salary_min": item.get("salary_min"),
                "salary_max": item.get("salary_max"),
                "posted_at": item.get("posted_at"),
                "url": item.get("url"),
                "skills": "|".join(match.skill for match in skill_matches),
                "skill_categories": "|".join(sorted({match.category for match in skill_matches})),
                "skill_match_terms": "|".join(_format_match_terms(skill_matches)),
                "skill_confidence": skill_confidence(skill_matches),
                "skill_count": len(skill_matches),
                "collected_at": record.collected_at.isoformat(),
            }
        )
    return pd.DataFrame(rows)


def normalize_course_listings(records: Iterable[RawRecord]) -> pd.DataFrame:
    rows = []
    for record in records:
        item = record.payload
        text = build_skill_text(
            item,
            ["title", "description", "subjects", "roles", "products", "platform"],
        )
        skill_matches = extract_skill_matches(text)
        rows.append(
            {
                "source_name": record.source_name,
                "source_confidence": confidence_for_source(record.source_name),
                "external_id": item.get("external_id"),
                "title": item.get("title"),
                "platform": item.get("platform"),
                "level": item.get("level"),
                "rating": item.get("rating"),
                "duration_minutes": item.get("duration_minutes"),
                "subjects": item.get("subjects"),
                "roles": item.get("roles"),
                "products": item.get("products"),
                "last_modified": item.get("last_modified"),
                "url": item.get("url"),
                "skills": "|".join(match.skill for match in skill_matches),
                "skill_categories": "|".join(sorted({match.category for match in skill_matches})),
                "skill_match_terms": "|".join(_format_match_terms(skill_matches)),
                "skill_confidence": skill_confidence(skill_matches),
                "skill_count": len(skill_matches),
                "collected_at": record.collected_at.isoformat(),
            }
        )
    return pd.DataFrame(rows)


def _skill_counts(df: pd.DataFrame) -> Counter[str]:
    counts: Counter[str] = Counter()
    if df.empty or "skills" not in df:
        return counts

    for skill_text in df["skills"].fillna(""):
        for skill in str(skill_text).split("|"):
            if skill:
                counts[skill] += 1
    return counts


def build_skill_gap_summary(jobs_df: pd.DataFrame, courses_df: pd.DataFrame) -> pd.DataFrame:
    job_counts = _skill_counts(jobs_df)
    course_counts = _skill_counts(courses_df)
    skills = sorted(set(job_counts) | set(course_counts))
    category_lookup = {definition.skill: definition.category for definition in SKILL_DEFINITIONS}
    max_job_demand = max(job_counts.values(), default=0)
    max_course_supply = max(course_counts.values(), default=0)
    salary_baseline = _salary_baseline(jobs_df)

    rows = []
    for skill in skills:
        job_demand = job_counts.get(skill, 0)
        course_supply = course_counts.get(skill, 0)
        market_signal = SKILL_MARKET_SIGNALS.get(skill, DEFAULT_MARKET_SIGNAL)
        onet_profile = onet_profile_for_skill(skill)
        growth_score = onet_growth_score(skill) or market_signal.growth_score
        demand_score = _normalize_count(job_demand, max_job_demand)
        course_supply_score = _normalize_count(course_supply, max_course_supply)
        salary_premium_score = _salary_premium_score(jobs_df, skill, salary_baseline, market_signal)
        opportunity_index = _opportunity_index(
            demand_score=demand_score,
            growth_score=growth_score,
            salary_premium_score=salary_premium_score,
            course_supply_score=course_supply_score,
            saturation_score=market_signal.saturation_score,
        )
        gap_score = job_demand - course_supply
        demand_supply_ratio = round(job_demand / course_supply, 2) if course_supply else None
        rows.append(
            {
                "skill": skill,
                "category": category_lookup.get(skill, "Other"),
                "job_demand": job_demand,
                "course_supply": course_supply,
                "gap_score": gap_score,
                "demand_supply_ratio": demand_supply_ratio,
                "demand_score": demand_score,
                "growth_score": growth_score,
                "salary_premium_score": salary_premium_score,
                "course_supply_score": course_supply_score,
                "saturation_score": market_signal.saturation_score,
                "opportunity_index": opportunity_index,
                "opportunity_label": _opportunity_label(opportunity_index),
                "market_direction": market_signal.market_direction,
                "target_job_roles": _target_job_roles(skill),
                "taxonomy_source": onet_profile.taxonomy_source if onet_profile else "Project fallback taxonomy",
                "onet_evidence_status": onet_profile.evidence_status if onet_profile else "project_fallback",
                "onet_workplace_examples": " | ".join(onet_profile.onet_workplace_examples) if onet_profile else "",
                "onet_soc_codes": onet_profile.soc_codes if onet_profile else "",
                "onet_occupations": onet_profile.occupation_titles if onet_profile else "",
                "onet_wage_median_annual": onet_profile.median_wage_annual if onet_profile else None,
                "onet_growth_outlook": onet_profile.growth_outlook if onet_profile else "",
                "bls_growth_percent": onet_profile.growth_percent if onet_profile else None,
                "bls_wage_year": 2024 if onet_profile else None,
                "bls_projection_period": "2024-2034" if onet_profile else "",
                "onet_projected_openings": onet_profile.projected_openings if onet_profile else None,
                "onet_reference_url": onet_profile.source_urls if onet_profile else "",
                "status": _gap_status(gap_score),
            }
        )

    return pd.DataFrame(rows).sort_values(
        ["opportunity_index", "gap_score", "job_demand"],
        ascending=[False, False, False],
    )


def build_skill_trend_history(jobs_df: pd.DataFrame, courses_df: pd.DataFrame, run_id: str) -> pd.DataFrame:
    """Build one trend-history table for the current run."""
    columns = [
        "run_id",
        "run_timestamp",
        "source_name",
        "skill",
        "job_count",
        "course_count",
        "salary_min_avg",
        "salary_max_avg",
        "location",
        "role_category",
    ]
    if jobs_df.empty or "skills" not in jobs_df:
        return pd.DataFrame(columns=columns)

    course_counts = _skill_counts(courses_df)
    run_timestamp_value = _run_timestamp_from_id(run_id)
    rows: list[dict[str, object]] = []

    for job in jobs_df.to_dict(orient="records"):
        for skill in _split_skills(job.get("skills")):
            rows.append(
                {
                    "run_id": run_id,
                    "run_timestamp": run_timestamp_value,
                    "source_name": job.get("source_name") or "unknown",
                    "skill": skill,
                    "location": job.get("location") or "Unknown",
                    "role_category": infer_role_category(str(job.get("title") or "")),
                    "salary_min": job.get("salary_min"),
                    "salary_max": job.get("salary_max"),
                    "course_count": course_counts.get(skill, 0),
                }
            )

    if not rows:
        return pd.DataFrame(columns=columns)

    exploded = pd.DataFrame(rows)
    grouped = (
        exploded.groupby(["run_id", "run_timestamp", "source_name", "skill", "location", "role_category"], dropna=False)
        .agg(
            job_count=("skill", "size"),
            course_count=("course_count", "max"),
            salary_min_avg=("salary_min", "mean"),
            salary_max_avg=("salary_max", "mean"),
        )
        .reset_index()
    )
    grouped["salary_min_avg"] = grouped["salary_min_avg"].round(2)
    grouped["salary_max_avg"] = grouped["salary_max_avg"].round(2)
    return grouped[columns].sort_values(
        ["run_timestamp", "skill", "job_count"],
        ascending=[True, True, False],
    )


def _gap_status(gap_score: int) -> str:
    if gap_score >= 2:
        return "High opportunity"
    if gap_score == 1:
        return "Emerging opportunity"
    if gap_score == 0:
        return "Balanced"
    return "Course-heavy"


def infer_role_category(title: str) -> str:
    normalized = title.lower()
    if any(term in normalized for term in ["engineer", "etl", "pipeline", "warehouse"]):
        return "Data Engineering"
    if any(term in normalized for term in ["scientist", "machine learning", "ml ", "ai "]):
        return "Data Science"
    if any(term in normalized for term in ["analyst", "analytics", "business intelligence", "bi "]):
        return "Data Analytics"
    if any(term in normalized for term in ["architect", "platform"]):
        return "Data Architecture"
    return "Other Data Role"


def _run_timestamp_from_id(run_id: str) -> str:
    try:
        timestamp = pd.to_datetime(run_id, format="%Y%m%d_%H%M%S", utc=True)
    except (TypeError, ValueError):
        return run_id
    return timestamp.isoformat()


def _split_skills(skill_text: object) -> list[str]:
    if skill_text is None or pd.isna(skill_text):
        return []
    return [skill for skill in str(skill_text).split("|") if skill]


def _normalize_count(value: int, max_value: int) -> int:
    if max_value <= 0:
        return 0
    return round((value / max_value) * 100)


def _opportunity_index(
    demand_score: int,
    growth_score: int,
    salary_premium_score: int,
    course_supply_score: int,
    saturation_score: int,
) -> int:
    score = (
        50
        + (0.35 * demand_score)
        + (0.25 * growth_score)
        + (0.25 * salary_premium_score)
        - (0.20 * course_supply_score)
        - (0.15 * saturation_score)
    )
    return max(0, min(100, round(score)))


def _opportunity_label(opportunity_index: int) -> str:
    if opportunity_index >= 75:
        return "High-value"
    if opportunity_index >= 60:
        return "Good bet"
    if opportunity_index >= 45:
        return "Balanced"
    return "Lower priority"


def _target_job_roles(skill: str) -> str:
    role_map = {
        "SQL": ["Data Analyst", "BI Analyst", "Analytics Engineer", "Data Engineer"],
        "Python": ["Data Analyst", "Data Scientist", "Data Engineer", "ML Engineer"],
        "Power BI": ["Data Analyst", "BI Developer", "Reporting Analyst"],
        "Tableau": ["Data Analyst", "BI Analyst", "Visualization Specialist"],
        "Excel": ["Data Analyst", "Business Analyst", "Operations Analyst"],
        "Airflow": ["Data Engineer", "Analytics Engineer", "Platform Engineer"],
        "dbt": ["Analytics Engineer", "Data Engineer", "BI Engineer"],
        "Spark": ["Data Engineer", "Big Data Engineer", "Data Platform Engineer"],
        "Databricks": ["Data Engineer", "ML Engineer", "Lakehouse Engineer"],
        "Snowflake": ["Data Engineer", "Analytics Engineer", "Warehouse Engineer"],
        "AWS": ["Cloud Data Engineer", "Data Engineer", "ML Engineer"],
        "Azure": ["Azure Data Engineer", "BI Developer", "Cloud Data Engineer"],
        "GCP": ["Cloud Data Engineer", "ML Engineer", "Data Platform Engineer"],
        "Machine Learning": ["Data Scientist", "ML Engineer", "Applied Scientist"],
        "NLP": ["NLP Engineer", "Data Scientist", "ML Engineer"],
        "GenAI": ["GenAI Analyst", "AI Engineer", "Applied AI Engineer"],
        "LLMs": ["LLM Engineer", "AI Engineer", "Data Scientist"],
        "Data Quality": ["Data Engineer", "Data Governance Analyst", "Analytics Engineer"],
        "Statistics": ["Data Analyst", "Data Scientist", "Product Analyst"],
        "Forecasting": ["Data Scientist", "Planning Analyst", "Product Analyst"],
        "A/B Testing": ["Product Analyst", "Data Scientist", "Growth Analyst"],
        "APIs": ["Data Engineer", "Analytics Engineer", "Backend Data Developer"],
        "Docker": ["Data Engineer", "ML Engineer", "Data Platform Engineer"],
        "FastAPI": ["Data Engineer", "ML Platform Engineer", "Analytics API Developer"],
    }
    return " | ".join(role_map.get(skill, ["Data Analyst", "Data Engineer", "Data Scientist"]))


def _salary_baseline(jobs_df: pd.DataFrame) -> float | None:
    salary_midpoints = _salary_midpoints(jobs_df)
    if salary_midpoints.empty:
        return None
    return float(salary_midpoints.median())


def _salary_premium_score(
    jobs_df: pd.DataFrame,
    skill: str,
    salary_baseline: float | None,
    market_signal: SkillMarketSignal,
) -> int:
    official_score = onet_salary_score(skill)
    if official_score is not None:
        return official_score

    if salary_baseline is None or salary_baseline <= 0:
        return market_signal.salary_premium_score

    jobs_with_skill = jobs_df[jobs_df["skills"].fillna("").str.contains(rf"(?:^|\|){re.escape(skill)}(?:\||$)", regex=True)]
    skill_midpoints = _salary_midpoints(jobs_with_skill)
    if skill_midpoints.empty:
        return market_signal.salary_premium_score

    premium_ratio = (float(skill_midpoints.median()) - salary_baseline) / salary_baseline
    calculated_score = round(50 + (premium_ratio * 100))
    return max(0, min(100, calculated_score))


def _salary_midpoints(jobs_df: pd.DataFrame) -> pd.Series:
    if jobs_df.empty or not {"salary_min", "salary_max"}.issubset(jobs_df.columns):
        return pd.Series(dtype="float64")

    salary_min = pd.to_numeric(jobs_df["salary_min"], errors="coerce")
    salary_max = pd.to_numeric(jobs_df["salary_max"], errors="coerce")
    midpoints = (salary_min + salary_max) / 2
    return midpoints.dropna()


def build_skill_text(item: dict, fields: list[str]) -> str:
    values: list[str] = []
    for field in fields:
        value = item.get(field)
        if value is None:
            continue
        values.append(str(value).replace("|", " "))
    return " ".join(values)


def skill_confidence(matches: list[SkillMatch]) -> float:
    if not matches:
        return 0.0
    return round(sum(match.confidence for match in matches) / len(matches), 2)


def _format_match_terms(matches: list[SkillMatch]) -> list[str]:
    return [f"{match.skill}:{','.join(match.matched_terms)}" for match in matches]
