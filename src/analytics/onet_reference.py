from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OnetOccupation:
    soc_code: str
    title: str
    median_wage_annual: int
    growth_outlook: str
    projected_openings: int
    growth_percent: float
    bls_url: str
    source_url: str


@dataclass(frozen=True)
class OnetSkillProfile:
    skill: str
    occupations: tuple[OnetOccupation, ...]
    @property
    def onet_workplace_examples(self) -> tuple[str, ...]:
        return ONET_SOFTWARE_SKILL_EXAMPLES.get(self.skill, ())

    @property
    def evidence_status(self) -> str:
        return "software_skill_verified" if self.onet_workplace_examples else "occupation_mapping_only"

    @property
    def taxonomy_source(self) -> str:
        if self.onet_workplace_examples:
            return "O*NET Software Skills 30.3 + BLS wage/projection references"
        return "SkillSync occupation mapping + O*NET-SOC + BLS wage/projection references"


    @property
    def soc_codes(self) -> str:
        return " | ".join(occupation.soc_code for occupation in self.occupations)

    @property
    def occupation_titles(self) -> str:
        return " | ".join(occupation.title for occupation in self.occupations)

    @property
    def source_urls(self) -> str:
        urls = {occupation.source_url for occupation in self.occupations}
        urls.update(occupation.bls_url for occupation in self.occupations)
        return " | ".join(sorted(urls))

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

    @property
    def growth_percent(self) -> float:
        rates = [occupation.growth_percent for occupation in self.occupations]
        return round(sum(rates) / len(rates), 1) if rates else 0.0


# Exact workplace-example labels in the O*NET 30.3 Software Skills download.
# Conceptual skills intentionally remain occupation_mapping_only.
ONET_SOFTWARE_SKILL_EXAMPLES: dict[str, tuple[str, ...]] = {
    "Python": ("Python",),
    "PostgreSQL": ("PostgreSQL",),
    "MySQL": ("MySQL",),
    "SQL Server": ("Microsoft SQL Server",),
    "Airflow": ("Apache Airflow",),
    "Spark": ("Apache Spark", "PySpark"),
    "Snowflake": ("Snowflake",),
    "AWS": ("Amazon Web Services AWS software",),
    "Azure": ("Microsoft Azure software",),
    "GCP": ("Google Cloud software",),
    "Power BI": ("Microsoft Power BI",),
    "Tableau": ("Tableau",),
    "Excel": ("Microsoft Excel",),
    "scikit-learn": ("Scikit-learn",),
    "TensorFlow": ("TensorFlow",),
    "PyTorch": ("PyTorch",),
    "pandas": ("pandas",),
    "NumPy": ("NumPy",),
    "Docker": ("Docker",),
    "Git": ("Git", "GitHub"),
}


DATA_SCIENTIST = OnetOccupation(
    soc_code="15-2051.00",
    title="Data Scientists",
    median_wage_annual=112590,
    growth_outlook="Much faster than average",
    projected_openings=23400,
    growth_percent=34.0,
    bls_url="https://www.bls.gov/ooh/math/data-scientists.htm",
    source_url="https://www.onetonline.org/link/summary/15-2051.00",
)

BUSINESS_INTELLIGENCE_ANALYST = OnetOccupation(
    soc_code="15-2051.01",
    title="Business Intelligence Analysts",
    median_wage_annual=112590,
    growth_outlook="Much faster than average",
    projected_openings=23400,
    growth_percent=34.0,
    bls_url="https://www.bls.gov/ooh/math/data-scientists.htm",
    source_url="https://www.onetonline.org/link/summary/15-2051.01",
)

DATABASE_ARCHITECT = OnetOccupation(
    soc_code="15-1243.00",
    title="Database Architects",
    median_wage_annual=135980,
    growth_outlook="Faster than average",
    projected_openings=4000,
    growth_percent=8.7,
    bls_url="https://www.bls.gov/emp/tables/occupational-projections-and-characteristics.htm",
    source_url="https://www.onetonline.org/link/summary/15-1243.00",
)

SOFTWARE_DEVELOPER = OnetOccupation(
    soc_code="15-1252.00",
    title="Software Developers",
    median_wage_annual=133080,
    growth_outlook="Much faster than average",
    projected_openings=129200,
    growth_percent=15.8,
    bls_url="https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm",
    source_url="https://www.onetonline.org/link/summary/15-1252.00",
)

STATISTICIAN = OnetOccupation(
    soc_code="15-2041.00",
    title="Statisticians",
    median_wage_annual=103300,
    growth_outlook="Much faster than average",
    projected_openings=2200,
    growth_percent=8.5,
    bls_url="https://www.bls.gov/ooh/math/mathematicians-and-statisticians.htm",
    source_url="https://www.onetonline.org/link/summary/15-2041.00",
)

MANAGEMENT_ANALYST = OnetOccupation(
    soc_code="13-1111.00",
    title="Management Analysts",
    median_wage_annual=101190,
    growth_outlook="Much faster than average",
    projected_openings=98100,
    growth_percent=9.0,
    bls_url="https://www.bls.gov/ooh/business-and-financial/management-analysts.htm",
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

    rates = [occupation.growth_percent for occupation in profile.occupations]
    average_growth = sum(rates) / len(rates)
    # Scale 0-35% projected growth into a bounded 40-90 score.
    return max(40, min(90, round(40 + (average_growth / 35 * 50))))
