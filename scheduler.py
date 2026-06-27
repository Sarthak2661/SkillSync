from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from pipeline import run_pipeline
from src.config.settings import settings


LOG_DIR = Path("logs")
LOG_PATH = LOG_DIR / "scheduler.log"


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def run_once() -> None:
    started_at = datetime.now(timezone.utc).isoformat()
    logging.info("Pipeline scheduled run started at %s", started_at)
    outputs = run_pipeline()
    logging.info("Pipeline scheduled run completed: %s", outputs)


def main() -> None:
    configure_logging()

    interval_seconds = max(settings.schedule_interval_minutes, 1) * 60
    logging.info(
        "Scheduler started with interval=%s minutes, run_on_start=%s",
        settings.schedule_interval_minutes,
        settings.scheduler_run_on_start,
    )

    if settings.scheduler_run_on_start:
        try:
            run_once()
        except Exception:
            logging.exception("Scheduled pipeline run failed.")

    while True:
        time.sleep(interval_seconds)
        try:
            run_once()
        except Exception:
            logging.exception("Scheduled pipeline run failed.")


if __name__ == "__main__":
    main()
