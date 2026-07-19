from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_prefix="MARKET_INTEL_",
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_url: str | None = None
    user_agent: str = "JobMarketSkillGapBot/0.1"
    raw_dir: Path = PROJECT_ROOT / "data" / "raw"
    processed_dir: Path = PROJECT_ROOT / "data" / "processed"
    api_data_limit: int = 500
    load_to_postgres: bool = False
    job_source_mode: str = "seed"
    job_source_url: str = "https://realpython.github.io/fake-jobs/"
    course_source_mode: str = "hybrid"
    course_source_url: str = "https://learn.microsoft.com/api/catalog/?type=modules&locale=en-us"
    course_source_limit: int = 200
    youtube_api_key: str | None = None
    youtube_source_limit: int = 12
    adzuna_app_id: str | None = None
    adzuna_app_key: str | None = None
    adzuna_country: str = "us"
    job_api_source_limit: int = 25
    github_token: str | None = None
    github_repository_limit: int = 5
    github_cache_minutes: int = 15
    github_updated_within_days: int = 180
    schedule_interval_minutes: int = 60
    scheduler_run_on_start: bool = True


settings = Settings()
