from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

from src.config.settings import settings
from src.ingestion.base import RawRecord


def run_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def save_raw_records(records: Iterable[RawRecord], dataset_name: str, run_id: str) -> Path:
    settings.raw_dir.mkdir(parents=True, exist_ok=True)
    path = settings.raw_dir / f"{dataset_name}_{run_id}.jsonl"

    with path.open("w", encoding="utf-8") as f:
        for record in records:
            row = asdict(record)
            row["collected_at"] = record.collected_at.isoformat()
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    return path


def save_dataframe(df: pd.DataFrame, dataset_name: str, run_id: str) -> Path:
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    path = settings.processed_dir / f"{dataset_name}_{run_id}.csv"
    df.to_csv(path, index=False)
    return path


def latest_processed_file(dataset_name: str) -> Path | None:
    if not settings.processed_dir.exists():
        return None

    files = sorted(settings.processed_dir.glob(f"{dataset_name}_*.csv"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def read_latest_dataframe(dataset_name: str) -> pd.DataFrame:
    path = latest_processed_file(dataset_name)
    if path is None:
        return pd.DataFrame()
    return pd.read_csv(path)


def read_all_dataframes(dataset_name: str) -> pd.DataFrame:
    if not settings.processed_dir.exists():
        return pd.DataFrame()

    files = sorted(settings.processed_dir.glob(f"{dataset_name}_*.csv"), key=lambda p: p.stat().st_mtime)
    frames = [pd.read_csv(path) for path in files]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
