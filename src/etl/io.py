# src/etl/io.py

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict


# Resolve project root: .../web scraper/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def save_raw_records(records: List[Dict], name: str = "books") -> Path:
    """Save records to data/raw/<name>_YYYYmmdd_HHMMSS.json."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RAW_DIR / f"{name}_{ts}.json"

    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    return path
