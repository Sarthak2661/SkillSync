# Project Notes

These notes explain the choices that are easy to miss when reading the code.

## Live And Curated Sources

Live APIs make the dataset current, but their coverage changes from run to run. Curated records keep demos, tests, and screenshots repeatable. The dashboard exposes both through source modes instead of presenting them as equivalent evidence.

The live job path uses documented APIs from Adzuna, Arbeitnow, Remotive, and HN Algolia. HTML job-board scrapers are not part of the active source modes.

## Skill Extraction

Skill extraction uses maintained regex patterns. It is deterministic, inexpensive, and straightforward to test. The tradeoff is lower recall when a posting uses an unexpected synonym or vague wording.

## Opportunity Scoring

The opportunity index combines observed demand and course supply with wage and growth references. O*NET-SOC mappings provide wage and outlook inputs where a skill maps cleanly to a data occupation. Maintained fallback values cover skills without a useful mapping.

The score is a ranking aid, not a labor-market forecast. Salary currencies, geography, source coverage, and limited history still affect the result.

## Historical Trends

Each successful run appends a skill snapshot. Early trend views are descriptive because the repository does not yet contain enough history for reliable forecasting. The local scheduler and Airflow DAG use the same pipeline steps, so either route produces compatible history.
