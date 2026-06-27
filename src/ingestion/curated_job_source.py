from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from src.config.settings import PROJECT_ROOT
from src.ingestion.base import RawRecord, SourceConnector, utc_now


DEFAULT_CURATED_JOBS_PATH = PROJECT_ROOT / "data" / "sample" / "curated_data_jobs.csv"


class CuratedDataJobsSource(SourceConnector):
    """Read the local sample job dataset."""

    source_name = "curated_data_jobs"
    source_type = "job_posting"

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_CURATED_JOBS_PATH

    def fetch(self) -> list[RawRecord]:
        collected_at = utc_now()
        records = _read_curated_jobs(self.path)

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


def _read_curated_jobs(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        for column in ["salary_min", "salary_max"]:
            row[column] = int(row[column]) if row.get(column) else None

    return rows
