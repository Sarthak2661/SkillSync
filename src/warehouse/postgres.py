from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import Any

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from src.config.settings import settings


SCHEMA_NAME = "market_intel"


DDL_STATEMENTS = (
    f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME};",
    f"""
    CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.job_postings (
        run_id TEXT NOT NULL,
        source_name TEXT,
        external_id TEXT,
        title TEXT,
        company TEXT,
        location TEXT,
        remote_type TEXT,
        salary_min NUMERIC,
        salary_max NUMERIC,
        posted_at TEXT,
        url TEXT,
        skills TEXT,
        skill_categories TEXT,
        skill_match_terms TEXT,
        skill_confidence NUMERIC,
        skill_count INT,
        collected_at TIMESTAMPTZ,
        loaded_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (run_id, source_name, external_id)
    );
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.course_listings (
        run_id TEXT NOT NULL,
        source_name TEXT,
        external_id TEXT,
        title TEXT,
        platform TEXT,
        level TEXT,
        rating NUMERIC,
        duration_minutes NUMERIC,
        subjects TEXT,
        roles TEXT,
        products TEXT,
        last_modified TEXT,
        url TEXT,
        skills TEXT,
        skill_categories TEXT,
        skill_match_terms TEXT,
        skill_confidence NUMERIC,
        skill_count INT,
        collected_at TIMESTAMPTZ,
        loaded_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (run_id, source_name, external_id)
    );
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.skill_gap_summary (
        run_id TEXT NOT NULL,
        skill TEXT NOT NULL,
        category TEXT,
        job_demand INT,
        course_supply INT,
        gap_score INT,
        demand_supply_ratio NUMERIC,
        demand_score INT,
        growth_score INT,
        salary_premium_score INT,
        course_supply_score INT,
        saturation_score INT,
        opportunity_index INT,
        opportunity_label TEXT,
        market_direction TEXT,
        target_job_roles TEXT,
        status TEXT,
        loaded_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (run_id, skill)
    );
    """,
    f"ALTER TABLE {SCHEMA_NAME}.skill_gap_summary ADD COLUMN IF NOT EXISTS demand_score INT;",
    f"ALTER TABLE {SCHEMA_NAME}.skill_gap_summary ADD COLUMN IF NOT EXISTS growth_score INT;",
    f"ALTER TABLE {SCHEMA_NAME}.skill_gap_summary ADD COLUMN IF NOT EXISTS salary_premium_score INT;",
    f"ALTER TABLE {SCHEMA_NAME}.skill_gap_summary ADD COLUMN IF NOT EXISTS course_supply_score INT;",
    f"ALTER TABLE {SCHEMA_NAME}.skill_gap_summary ADD COLUMN IF NOT EXISTS saturation_score INT;",
    f"ALTER TABLE {SCHEMA_NAME}.skill_gap_summary ADD COLUMN IF NOT EXISTS opportunity_index INT;",
    f"ALTER TABLE {SCHEMA_NAME}.skill_gap_summary ADD COLUMN IF NOT EXISTS opportunity_label TEXT;",
    f"ALTER TABLE {SCHEMA_NAME}.skill_gap_summary ADD COLUMN IF NOT EXISTS market_direction TEXT;",
    f"ALTER TABLE {SCHEMA_NAME}.skill_gap_summary ADD COLUMN IF NOT EXISTS target_job_roles TEXT;",
    f"""
    CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.quality_checks (
        run_id TEXT NOT NULL,
        dataset TEXT NOT NULL,
        check_name TEXT NOT NULL,
        status TEXT,
        severity TEXT,
        records_checked INT,
        failed_count INT,
        message TEXT,
        loaded_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (run_id, dataset, check_name)
    );
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.skill_trend_history (
        run_id TEXT NOT NULL,
        run_timestamp TIMESTAMPTZ,
        source_name TEXT NOT NULL,
        skill TEXT NOT NULL,
        job_count INT,
        course_count INT,
        salary_min_avg NUMERIC,
        salary_max_avg NUMERIC,
        location TEXT NOT NULL,
        role_category TEXT NOT NULL,
        loaded_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (run_id, source_name, skill, location, role_category)
    );
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.certification_recommendations (
        run_id TEXT NOT NULL,
        skill TEXT NOT NULL,
        certification_name TEXT NOT NULL,
        provider TEXT,
        level TEXT,
        free_or_paid TEXT,
        estimated_cost_usd NUMERIC,
        target_roles TEXT,
        url TEXT,
        priority_score INT,
        opportunity_index NUMERIC,
        opportunity_label TEXT,
        job_demand NUMERIC,
        target_job_roles TEXT,
        market_priority NUMERIC,
        recommendation_score INT,
        loaded_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (run_id, skill, certification_name)
    );
    """,
)


def load_pipeline_outputs(
    run_id: str,
    jobs_df: pd.DataFrame,
    courses_df: pd.DataFrame,
    skill_gap_df: pd.DataFrame,
    skill_trend_df: pd.DataFrame,
    certification_df: pd.DataFrame,
    quality_df: pd.DataFrame,
) -> None:
    if not settings.db_url:
        raise RuntimeError("MARKET_INTEL_DB_URL is required when MARKET_INTEL_LOAD_TO_POSTGRES=true.")

    with psycopg2.connect(settings.db_url) as conn:
        with conn.cursor() as cur:
            for statement in DDL_STATEMENTS:
                cur.execute(statement)

            _insert_dataframe(cur, f"{SCHEMA_NAME}.job_postings", run_id, jobs_df)
            _insert_dataframe(cur, f"{SCHEMA_NAME}.course_listings", run_id, courses_df)
            _insert_dataframe(cur, f"{SCHEMA_NAME}.skill_gap_summary", run_id, skill_gap_df)
            _insert_dataframe(cur, f"{SCHEMA_NAME}.skill_trend_history", None, skill_trend_df)
            _insert_dataframe(cur, f"{SCHEMA_NAME}.certification_recommendations", run_id, certification_df)
            _insert_dataframe(cur, f"{SCHEMA_NAME}.quality_checks", run_id, quality_df)


def _insert_dataframe(cur, table_name: str, run_id: str | None, df: pd.DataFrame) -> None:
    if df.empty:
        return

    df_to_load = df.copy()
    if run_id is not None:
        df_to_load.insert(0, "run_id", run_id)
    columns = list(df_to_load.columns)
    values = [_normalize_row(row) for row in df_to_load.itertuples(index=False, name=None)]

    column_sql = ", ".join(columns)
    sql = f"""
        INSERT INTO {table_name} ({column_sql})
        VALUES %s
        ON CONFLICT DO NOTHING
    """
    execute_values(cur, sql, values, page_size=500)


def _normalize_row(row: Iterable[Any]) -> tuple[Any, ...]:
    return tuple(_normalize_value(value) for value in row)


def _normalize_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, Decimal):
        return value
    if hasattr(value, "item"):
        return value.item()
    return value
