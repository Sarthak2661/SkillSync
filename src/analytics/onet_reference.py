from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OnetOccupation:
    soc_code: str
    title: str
    median_wage_annual: int
    growth_outlook: str
    projected_openings: int
    source_url: str


@dataclass(frozen=True)
class OnetSkillProfile:
    skill: str
    occupations: tuple[OnetOccupation, ...]
    taxonomy_source: str = "O*NET-SOC / BLS wage and projection data"

    @property
    def soc_codes(self) -> str:
        return " | ".join(occupation.soc_code for occupation in self.occupations)

    @property
    def occupation_titles(self) -> str:
        return " | ".join(occupation.title for occupation in self.occupations)

    @property
    def source_urls(self) -> str:
        return " | ".join(sorted({occupation.source_url for occupation in self.occupations}))

    @property
    def median_wage_annual(self) -> int:
        wages = [occupation.median_wage_annual for occupation in self.occupations]
        return round(sum(wages) / len(wages)) if wages else 0

    @property
    def growth_outlook(self) -> str:
        outlooks = sorted({occupation.growth_outlook for occupation in self.occupations})
        return " | ".join(outlooks)

    @property
    def projected_openings(self) -> int:
        return sum(occupation.projected_openings for occupation in self.occupations)


DATA_SCIENTIST = OnetOccupation(
    soc_code="15-2051.00",
    title="Data Scientists",
    median_wage_annual=120230,
    growth_outlook="Much faster than average",
    projected_openings=23400,
    source_url="https://www.onetonline.org/link/summary/15-2051.00",
)

BUSINESS_INTELLIGENCE_ANALYST = OnetOccupation(
    soc_code="15-2051.01",
    title="Business Intelligence Analysts",
    median_wage_annual=120230,
    growth_outlook="Much faster than average",
    projected_openings=23400,
    source_url="https://www.onetonline.org/link/summary/15-2051.01",
)

DATABASE_ARCHITECT = OnetOccupation(
    soc_code="15-1243.00",
    title="Database Architects",
    median_wage_annual=139500,
    growth_outlook="Much faster than average",
    projected_openings=4000,
    source_url="https://www.onetonline.org/link/summary/15-1243.00",
)

SOFTWARE_DEVELOPER = OnetOccupation(
    soc_code="15-1252.00",
    title="Software Developers",
    median_wage_annual=135980,
    growth_outlook="Much faster than average",
    projected_openings=115200,
    source_url="https://www.onetonline.org/link/summary/15-1252.00",
)

STATISTICIAN = OnetOccupation(
    soc_code="15-2041.00",
    title="Statisticians",
    median_wage_annual=105650,
    growth_outlook="Much faster than average",
    projected_openings=2000,
    source_url="https://www.onetonline.org/link/summary/15-2041.00",
)

MANAGEMENT_ANALYST = OnetOccupation(
    soc_code="13-1111.00",
    title="Management Analysts",
    median_wage_annual=101860,
    growth_outlook="Much faster than average",
    projected_openings=98100,
    source_url="https://www.onetonline.org/link/summary/13-1111.00",
)


ONET_SKILL_PROFILES: dict[str, OnetSkillProfile] = {
    "Python": OnetSkillProfile("Python", (DATA_SCIENTIST, SOFTWARE_DEVELOPER)),
    "R": OnetSkillProfile("R", (DATA_SCIENTIST, STATISTICIAN)),
    "SQL": OnetSkillProfile("SQL", (BUSINESS_INTELLIGENCE_ANALYST, DATABASE_ARCHITECT)),
    "PostgreSQL": OnetSkillProfile("PostgreSQL", (DATABASE_ARCHITECT, DATA_SCIENTIST)),
    "MySQL": OnetSkillProfile("MySQL", (DATABASE_ARCHITECT, SOFTWARE_DEVELOPER)),
    "SQL Server": OnetSkillProfile("SQL Server", (DATABASE_ARCHITECT, BUSINESS_INTELLIGENCE_ANALYST)),
    "NoSQL": OnetSkillProfile("NoSQL", (DATABASE_ARCHITECT, SOFTWARE_DEVELOPER)),
    "Data Modeling": OnetSkillProfile("Data Modeling", (DATABASE_ARCHITECT,)),
    "ETL": OnetSkillProfile("ETL", (DATABASE_ARCHITECT, BUSINESS_INTELLIGENCE_ANALYST)),
    "ELT": OnetSkillProfile("ELT", (DATABASE_ARCHITECT, BUSINESS_INTELLIGENCE_ANALYST)),
    "Data Pipelines": OnetSkillProfile("Data Pipelines", (DATABASE_ARCHITECT, SOFTWARE_DEVELOPER)),
    "Airflow": OnetSkillProfile("Airflow", (DATA_SCIENTIST, DATABASE_ARCHITECT)),
    "dbt": OnetSkillProfile("dbt", (BUSINESS_INTELLIGENCE_ANALYST, DATABASE_ARCHITECT)),
    "Spark": OnetSkillProfile("Spark", (DATA_SCIENTIST, DATABASE_ARCHITECT)),
    "Databricks": OnetSkillProfile("Databricks", (DATA_SCIENTIST, DATABASE_ARCHITECT)),
    "Snowflake": OnetSkillProfile("Snowflake", (DATABASE_ARCHITECT, BUSINESS_INTELLIGENCE_ANALYST)),
    "Azure Data Factory": OnetSkillProfile("Azure Data Factory", (DATABASE_ARCHITECT, SOFTWARE_DEVELOPER)),
    "Microsoft Fabric": OnetSkillProfile("Microsoft Fabric", (BUSINESS_INTELLIGENCE_ANALYST, DATABASE_ARCHITECT)),
    "AWS": OnetSkillProfile("AWS", (SOFTWARE_DEVELOPER, DATABASE_ARCHITECT)),
    "Azure": OnetSkillProfile("Azure", (SOFTWARE_DEVELOPER, DATABASE_ARCHITECT)),
    "GCP": OnetSkillProfile("GCP", (SOFTWARE_DEVELOPER, DATA_SCIENTIST)),
    "Power BI": OnetSkillProfile("Power BI", (BUSINESS_INTELLIGENCE_ANALYST, MANAGEMENT_ANALYST)),
    "Tableau": OnetSkillProfile("Tableau", (BUSINESS_INTELLIGENCE_ANALYST, DATA_SCIENTIST)),
    "Excel": OnetSkillProfile("Excel", (BUSINESS_INTELLIGENCE_ANALYST, MANAGEMENT_ANALYST)),
    "Data Visualization": OnetSkillProfile("Data Visualization", (BUSINESS_INTELLIGENCE_ANALYST, DATA_SCIENTIST)),
    "Machine Learning": OnetSkillProfile("Machine Learning", (DATA_SCIENTIST, SOFTWARE_DEVELOPER)),
    "Deep Learning": OnetSkillProfile("Deep Learning", (DATA_SCIENTIST, SOFTWARE_DEVELOPER)),
    "NLP": OnetSkillProfile("NLP", (DATA_SCIENTIST, SOFTWARE_DEVELOPER)),
    "GenAI": OnetSkillProfile("GenAI", (DATA_SCIENTIST, SOFTWARE_DEVELOPER)),
    "LLMs": OnetSkillProfile("LLMs", (DATA_SCIENTIST, SOFTWARE_DEVELOPER)),
    "scikit-learn": OnetSkillProfile("scikit-learn", (DATA_SCIENTIST,)),
    "TensorFlow": OnetSkillProfile("TensorFlow", (DATA_SCIENTIST, SOFTWARE_DEVELOPER)),
    "PyTorch": OnetSkillProfile("PyTorch", (DATA_SCIENTIST, SOFTWARE_DEVELOPER)),
    "pandas": OnetSkillProfile("pandas", (DATA_SCIENTIST,)),
    "NumPy": OnetSkillProfile("NumPy", (DATA_SCIENTIST, STATISTICIAN)),
    "Matplotlib": OnetSkillProfile("Matplotlib", (DATA_SCIENTIST, STATISTICIAN)),
    "Seaborn": OnetSkillProfile("Seaborn", (DATA_SCIENTIST, STATISTICIAN)),
    "Statistics": OnetSkillProfile("Statistics", (STATISTICIAN, DATA_SCIENTIST)),
    "A/B Testing": OnetSkillProfile("A/B Testing", (STATISTICIAN, BUSINESS_INTELLIGENCE_ANALYST)),
    "Forecasting": OnetSkillProfile("Forecasting", (STATISTICIAN, MANAGEMENT_ANALYST)),
    "APIs": OnetSkillProfile("APIs", (SOFTWARE_DEVELOPER, DATA_SCIENTIST)),
    "Docker": OnetSkillProfile("Docker", (SOFTWARE_DEVELOPER, DATABASE_ARCHITECT)),
    "Git": OnetSkillProfile("Git", (SOFTWARE_DEVELOPER, DATA_SCIENTIST)),
    "FastAPI": OnetSkillProfile("FastAPI", (SOFTWARE_DEVELOPER, DATA_SCIENTIST)),
    "Data Quality": OnetSkillProfile("Data Quality", (DATABASE_ARCHITECT, BUSINESS_INTELLIGENCE_ANALYST)),
    "Responsible AI": OnetSkillProfile("Responsible AI", (DATA_SCIENTIST, SOFTWARE_DEVELOPER)),
}


def onet_profile_for_skill(skill: str) -> OnetSkillProfile | None:
    return ONET_SKILL_PROFILES.get(skill)


def onet_salary_score(skill: str) -> int | None:
    profile = onet_profile_for_skill(skill)
    if profile is None:
        return None

    wages = [profile.median_wage_annual for profile in ONET_SKILL_PROFILES.values()]
    low = min(wages)
    high = max(wages)
    if high <= low:
        return 50

    normalized = (profile.median_wage_annual - low) / (high - low)
    return round(40 + (normalized * 45))


def onet_growth_score(skill: str) -> int | None:
    profile = onet_profile_for_skill(skill)
    if profile is None:
        return None

    outlook = profile.growth_outlook.lower()
    if "much faster" in outlook:
        return 80
    if "faster" in outlook:
        return 70
    if "average" in outlook:
        return 55
    if "slower" in outlook:
        return 35
    return 50
