from __future__ import annotations

from typing import Any

import pandas as pd


def build_weekly_reports(
    trends: pd.DataFrame,
    skill_gaps: pd.DataFrame,
    runs: pd.DataFrame,
    limit: int = 12,
) -> list[dict[str, Any]]:
    """Build one market briefing from the latest retained snapshot in each week."""
    required = {"run_id", "run_timestamp", "skill", "job_count"}
    if trends.empty or not required.issubset(trends.columns):
        return []

    history = trends.copy()
    history["run_id"] = history["run_id"].astype(str)
    history["run_timestamp"] = pd.to_datetime(history["run_timestamp"], errors="coerce", utc=True)
    history = history.dropna(subset=["run_timestamp", "skill"])
    if history.empty:
        return []

    history["job_count"] = pd.to_numeric(history["job_count"], errors="coerce").fillna(0)
    if "course_count" not in history:
        history["course_count"] = 0
    history["course_count"] = pd.to_numeric(history["course_count"], errors="coerce").fillna(0)
    if "role_family" not in history:
        history["role_family"] = ""

    run_times = history.groupby("run_id", as_index=False)["run_timestamp"].max()
    local_dates = run_times["run_timestamp"].dt.tz_convert(None)
    run_times["week_start"] = local_dates.dt.to_period("W-SUN").dt.start_time
    selected = (
        run_times.sort_values("run_timestamp")
        .groupby("week_start", as_index=False)
        .tail(1)
        .sort_values("run_timestamp")
    )

    snapshots = {
        run_id: _aggregate_snapshot(history[history["run_id"] == run_id])
        for run_id in selected["run_id"]
    }
    run_lookup = _run_lookup(runs)
    opportunity_lookup = _opportunity_lookup(skill_gaps)
    reports: list[dict[str, Any]] = []
    selected_rows = list(selected.itertuples(index=False))

    for index, row in enumerate(selected_rows):
        current = snapshots[row.run_id]
        previous = snapshots[selected_rows[index - 1].run_id] if index else pd.DataFrame()
        top_skills = _top_skills(current, opportunity_lookup)
        rising, declining = _movement(current, previous)
        run = run_lookup.get(row.run_id, {})
        top_skill = top_skills[0]["skill"] if top_skills else str(run.get("top_opportunity_skill") or "No skill")
        jobs = int(_number(run.get("job_records"), current["job_count"].sum() if not current.empty else 0))
        courses = int(_number(run.get("course_records"), current["course_count"].max() if not current.empty else 0))
        skills = int(_number(run.get("unique_skills"), current["skill"].nunique() if not current.empty else 0))
        published = pd.Timestamp(row.run_timestamp)
        week_start = pd.Timestamp(row.week_start)
        week_end = week_start + pd.Timedelta(days=6)
        change_text = (
            f"{rising[0]['skill']} recorded the largest increase from the previous retained week."
            if rising
            else "This is the first retained weekly baseline, so no week-over-week movement is shown yet."
        )
        reports.append(
            {
                "report_id": f"{week_start:%Y-%m-%d}-{row.run_id}",
                "run_id": row.run_id,
                "published_at": published.isoformat(),
                "week_start": week_start.date().isoformat(),
                "week_end": week_end.date().isoformat(),
                "title": f"{top_skill} leads the weekly technology skill snapshot",
                "summary": (
                    f"The latest retained snapshot includes {jobs:,} jobs, {courses:,} learning resources, "
                    f"and {skills:,} scored skills. {change_text}"
                ),
                "jobs": jobs,
                "courses": courses,
                "skills": skills,
                "top_opportunity_skill": str(run.get("top_opportunity_skill") or top_skill),
                "top_skills": top_skills,
                "rising_skills": rising,
                "declining_skills": declining,
                "status": "Latest snapshot" if index == len(selected_rows) - 1 else "Archived snapshot",
                "methodology_note": (
                    "Directional analysis from retained SkillSync pipeline snapshots. "
                    "It is not a representative estimate of the full labor market."
                ),
            }
        )

    return list(reversed(reports[-limit:]))


def _aggregate_snapshot(rows: pd.DataFrame) -> pd.DataFrame:
    def families(values: pd.Series) -> str:
        found: set[str] = set()
        for value in values.dropna().astype(str):
            found.update(part.strip() for part in value.split("|") if part.strip())
        return " | ".join(sorted(found))

    return (
        rows.groupby("skill", as_index=False)
        .agg(job_count=("job_count", "sum"), course_count=("course_count", "max"), role_families=("role_family", families))
        .sort_values(["job_count", "skill"], ascending=[False, True])
    )


def _top_skills(snapshot: pd.DataFrame, opportunity_lookup: dict[str, float]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in snapshot.head(6).itertuples(index=False):
        rows.append(
            {
                "skill": item.skill,
                "job_count": int(item.job_count),
                "course_count": int(item.course_count),
                "role_families": item.role_families,
                "opportunity_index": opportunity_lookup.get(item.skill),
            }
        )
    return rows


def _movement(current: pd.DataFrame, previous: pd.DataFrame) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if previous.empty:
        return [], []
    comparison = current[["skill", "job_count"]].merge(
        previous[["skill", "job_count"]],
        on="skill",
        how="outer",
        suffixes=("_current", "_previous"),
    ).fillna(0)
    comparison["change"] = comparison["job_count_current"] - comparison["job_count_previous"]

    def records(rows: pd.DataFrame) -> list[dict[str, Any]]:
        return [
            {
                "skill": row.skill,
                "current": int(row.job_count_current),
                "previous": int(row.job_count_previous),
                "change": int(row.change),
            }
            for row in rows.itertuples(index=False)
        ]

    rising = comparison[comparison["change"] > 0].sort_values(["change", "skill"], ascending=[False, True]).head(5)
    declining = comparison[comparison["change"] < 0].sort_values(["change", "skill"], ascending=[True, True]).head(5)
    return records(rising), records(declining)


def _run_lookup(runs: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if runs.empty or "run_id" not in runs:
        return {}
    return {str(row["run_id"]): row for row in runs.to_dict(orient="records")}


def _opportunity_lookup(skill_gaps: pd.DataFrame) -> dict[str, float]:
    if skill_gaps.empty or not {"skill", "opportunity_index"}.issubset(skill_gaps.columns):
        return {}
    return {
        str(row.skill): float(row.opportunity_index)
        for row in skill_gaps[["skill", "opportunity_index"]].dropna().itertuples(index=False)
    }


def _number(value: Any, fallback: float) -> float:
    parsed = pd.to_numeric(value, errors="coerce")
    return float(parsed) if pd.notna(parsed) else float(fallback)
