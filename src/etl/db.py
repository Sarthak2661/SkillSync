# src/etl/db.py

from __future__ import annotations
from typing import List, Dict, Optional
from typing import Optional

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

from src.config.settings import settings


BOOKS_DDL = """
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title TEXT,
    price NUMERIC(8,2),
    currency TEXT,
    rating INT,
    availability_text TEXT,
    in_stock BOOLEAN,
    stock_count INT,
    product_url TEXT,
    scraped_at TIMESTAMPTZ
);
"""


def get_connection():
    if not settings.db_url:
        raise RuntimeError("WEBSCRAPER_DB_URL is not set in .env")
    return psycopg2.connect(settings.db_url)


def init_db() -> None:
    """Create the books table if it doesn't exist."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(BOOKS_DDL)
    print("Ensured 'books' table exists.")


def insert_books(df: pd.DataFrame) -> None:
    """Insert cleaned DataFrame rows into the books table."""
    records = df.to_dict(orient="records")

    sql = """
        INSERT INTO books
        (title, price, currency, rating, availability_text,
         in_stock, stock_count, product_url, scraped_at)
        VALUES
        (%(title)s, %(price)s, %(currency)s, %(rating)s, %(availability_text)s,
         %(in_stock)s, %(stock_count)s, %(product_url)s, %(scraped_at)s)
    """

    with get_connection() as conn, conn.cursor() as cur:
        execute_batch(cur, sql, records, page_size=100)
    print(f"Inserted {len(records)} rows into 'books' table.")




def fetch_books(limit: int = 50, min_rating: Optional[int] = None) -> List[Dict]:
    """
    Fetch books from DB with optional rating filter.
    Returns list[dict] for easy serialization.
    """
    base_sql = """
        SELECT
            title,
            price,
            currency,
            rating,
            availability_text,
            in_stock,
            stock_count,
            product_url,
            scraped_at
        FROM books
    """

    conditions = []
    params: list = []

    if min_rating is not None:
        conditions.append("rating >= %s")
        params.append(min_rating)

    if conditions:
        base_sql += " WHERE " + " AND ".join(conditions)

    base_sql += " ORDER BY price ASC NULLS LAST LIMIT %s"
    params.append(limit)

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(base_sql, params)
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    return rows


def fetch_price_stats() -> Dict:
    """
    Return simple price statistics for the books table.
    """
    sql = """
        SELECT
            COUNT(*) AS total_books,
            COUNT(price) AS priced_books,
            AVG(price) AS avg_price,
            MIN(price) AS min_price,
            MAX(price) AS max_price
        FROM books;
    """

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql)
        row = cur.fetchone()
        cols = [c[0] for c in cur.description]
        stats = dict(zip(cols, row))

    return stats

def search_books(
    query: str,
    limit: int = 50,
    min_rating: Optional[int] = None,
) -> List[Dict]:
    """
    Search for books whose title contains the given query (case-insensitive),
    with optional minimum rating.
    """
    sql = """
        SELECT
            title,
            price,
            currency,
            rating,
            availability_text,
            in_stock,
            stock_count,
            product_url,
            scraped_at
        FROM books
        WHERE title ILIKE %s
    """

    params: list = [f"%{query}%"]

    if min_rating is not None:
        sql += " AND rating >= %s"
        params.append(min_rating)

    sql += " ORDER BY price ASC NULLS LAST LIMIT %s"
    params.append(limit)

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    return rows