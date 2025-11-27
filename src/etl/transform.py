# src/etl/transform.py

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import pandas as pd

# Reuse the same root logic as io.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def normalize_records(raw_records: List[Dict]) -> pd.DataFrame:
    """
    Take list[dict] from the scraper and return a clean pandas DataFrame.
    """
    scraped_at = datetime.utcnow()
    rows = []

    for r in raw_records:
        price_text = (r.get("price_raw") or "").strip()

        if price_text:
            currency = price_text[0]
            try:
                price = float(price_text[1:].strip().replace("£", "").replace("$", ""))
            except ValueError:
                price = None
        else:
            currency = None
            price = None

        rating_raw = r.get("rating_raw")
        rating = RATING_MAP.get(rating_raw, None)

        availability_text = (r.get("availability_raw") or "").strip()

        in_stock = "In stock" in availability_text
        m = re.search(r"(\d+)", availability_text)
        stock_count = int(m.group(1)) if m else None

        rows.append(
            {
                "title": r.get("title"),
                "price": price,
                "currency": currency,
                "rating": rating,
                "availability_text": availability_text,
                "in_stock": in_stock,
                "stock_count": stock_count,
                "product_url": r.get("product_url"),
                "scraped_at": scraped_at,
            }
        )

    df = pd.DataFrame(rows)
    return df


def save_processed_df(df: pd.DataFrame, name: str = "books_clean") -> Path:
    """
    Save cleaned DataFrame to data/processed/<name>_YYYYmmdd_HHMMSS.csv
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = PROCESSED_DIR / f"{name}_{ts}.csv"
    df.to_csv(path, index=False)
    return path
