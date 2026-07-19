from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analytics.onet_reference import ONET_SKILL_PROFILES, ONET_SOFTWARE_SKILL_EXAMPLES

DEFAULT_URL = "https://www.onetcenter.org/dl_files/database/db_30_3_json/software_skills.json"


def build_evidence(source: dict) -> dict:
    rows = source["row"]
    expected = {(skill, example) for skill, examples in ONET_SOFTWARE_SKILL_EXAMPLES.items() for example in examples}
    matches = []
    for row in rows:
        for skill, example in expected:
            profile_codes = set(ONET_SKILL_PROFILES[skill].soc_codes.split(" | "))
            if row["workplace_example"] == example and row["onetsoc_code"] in profile_codes:
                matches.append({
                    "skill": skill,
                    "workplace_example": example,
                    "soc_code": row["onetsoc_code"],
                    "occupation": row["title"],
                    "hot_technology": row["hot_technology"] == "Y",
                    "in_demand": row["in_demand"] == "Y",
                })
    matched = {(row["skill"], row["workplace_example"]) for row in matches}
    missing = sorted(expected - matched)
    if missing:
        raise ValueError(f"O*NET evidence missing for {missing}")
    return {
        "source": DEFAULT_URL,
        "database_version": "30.3",
        "license": "CC BY 4.0",
        "attribution": "O*NET 30.3 Database, U.S. Department of Labor, Employment and Training Administration",
        "records": sorted(matches, key=lambda row: (row["skill"], row["soc_code"], row["workplace_example"])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh the compact O*NET evidence snapshot.")
    parser.add_argument("--input", type=Path, help="Use a downloaded Software Skills JSON file.")
    parser.add_argument("--output", type=Path, default=Path("data/reference/onet_software_skill_evidence.json"))
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8")) if args.input else json.load(urlopen(DEFAULT_URL))
    evidence = build_evidence(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2) + chr(10), encoding="utf-8")
    print(f"Wrote {len(evidence['records'])} verified O*NET records to {args.output}")


if __name__ == "__main__":
    main()
