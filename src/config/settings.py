# src/config/settings.py

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_prefix="WEBSCRAPER_",
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
    )

    db_url: str | None = None
    base_url: str = "https://books.toscrape.com"
    user_agent: str = "WebScraperBot/0.1 (+https://github.com/Sarthak2661/web-scraper)"

settings = Settings()
