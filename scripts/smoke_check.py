from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.analytics.model import build_kpis, latest_dataset_paths, load_latest_outputs


REQUIRED_DATASETS = {
    "job_postings_clean",
    "course_listings_clean",
    "skill_gap_summary",
    "skill_trend_history",
    "certification_recommendations",
    "quality_summary",
}


def main() -> None:
    paths = latest_dataset_paths()
    missing = [name for name in REQUIRED_DATASETS if not paths.get(name)]
    if missing:
        print("Missing processed outputs:")
        for name in sorted(missing):
            print(f"- {name}")
        print("\nRun `python pipeline.py` first.")
        raise SystemExit(1)

    outputs = load_latest_outputs()
    kpis = build_kpis(outputs)
    print("Latest SkillSync run looks readable.")
    print(f"Run ID: {kpis.get('run_id')}")
    print(f"Jobs: {kpis.get('job_postings')}")
    print(f"Courses: {kpis.get('course_listings')}")
    print(f"Skills: {kpis.get('unique_skills')}")
    print(f"Quality warnings: {kpis.get('quality_warnings')}")

    powerbi_dir = Path("powerbi/export")
    if powerbi_dir.exists():
        exported = sorted(path.name for path in powerbi_dir.glob("*.csv"))
        print(f"Power BI CSVs: {len(exported)} file(s)")
    else:
        print("Power BI export folder not found yet. Run `python export_powerbi.py` if needed.")


if __name__ == "__main__":
    main()
