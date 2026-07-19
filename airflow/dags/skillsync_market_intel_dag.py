from __future__ import annotations

from datetime import datetime, timedelta
import subprocess

from airflow import DAG
from airflow.operators.python import PythonOperator

from pipeline import get_course_source, get_job_source
from src.orchestration.pipeline_steps import (
    export_powerbi_files,
    ingest_sources,
    load_postgres_if_enabled,
    run_quality_checks,
    transform_raw_records,
    write_run_log_from_paths,
)


DEFAULT_ARGS = {
    "owner": "skillsync",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def ingest_task() -> dict[str, str]:
    return ingest_sources(get_job_source(), get_course_source())


def transform_task(**context) -> dict[str, str]:
    ingested = context["ti"].xcom_pull(task_ids="ingest")
    return transform_raw_records(
        raw_jobs_path=ingested["raw_jobs"],
        raw_courses_path=ingested["raw_courses"],
        run_id=ingested["run_id"],
    )


def quality_task(**context) -> dict[str, str]:
    ingested = context["ti"].xcom_pull(task_ids="ingest")
    transformed = context["ti"].xcom_pull(task_ids="transform")
    return run_quality_checks(
        clean_jobs_path=transformed["clean_jobs"],
        clean_courses_path=transformed["clean_courses"],
        skill_gap_path=transformed["skill_gap_summary"],
        run_id=ingested["run_id"],
    )


def postgres_load_task(**context) -> str:
    ingested = context["ti"].xcom_pull(task_ids="ingest")
    transformed = context["ti"].xcom_pull(task_ids="transform")
    quality = context["ti"].xcom_pull(task_ids="quality_checks")
    warehouse_status = load_postgres_if_enabled(
        clean_jobs_path=transformed["clean_jobs"],
        clean_courses_path=transformed["clean_courses"],
        skill_gap_path=transformed["skill_gap_summary"],
        skill_trend_path=transformed["skill_trend_history"],
        certification_path=transformed["certification_recommendations"],
        quality_path=quality["quality_summary"],
        run_id=ingested["run_id"],
    )
    write_run_log_from_paths(
        run_id=ingested["run_id"],
        clean_jobs_path=transformed["clean_jobs"],
        clean_courses_path=transformed["clean_courses"],
        skill_gap_path=transformed["skill_gap_summary"],
        skill_trend_path=transformed["skill_trend_history"],
        warehouse_status=warehouse_status,
    )
    return warehouse_status


def dbt_build_task() -> None:
    subprocess.run(
        [
            "dbt",
            "build",
            "--project-dir",
            "dbt",
            "--profiles-dir",
            "dbt",
        ],
        check=True,
    )


with DAG(
    dag_id="skillsync_market_intel_pipeline",
    default_args=DEFAULT_ARGS,
    description="Run the SkillSync job/course market intelligence pipeline.",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@hourly",
    catchup=False,
    tags=["skillsync", "etl", "portfolio"],
) as dag:
    ingest = PythonOperator(task_id="ingest", python_callable=ingest_task)
    transform = PythonOperator(task_id="transform", python_callable=transform_task)
    quality = PythonOperator(task_id="quality_checks", python_callable=quality_task)
    export_powerbi = PythonOperator(task_id="export_powerbi_files", python_callable=export_powerbi_files)
    postgres_load = PythonOperator(task_id="optional_postgresql_load", python_callable=postgres_load_task)
    dbt_build = PythonOperator(task_id="dbt_build_and_test", python_callable=dbt_build_task)

    ingest >> transform >> quality >> postgres_load >> dbt_build >> export_powerbi
