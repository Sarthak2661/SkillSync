# Source Notes

SkillSync uses official APIs for current records and curated local data for repeatable demos and tests. Parser-only sources are labeled separately so they are not mistaken for market evidence.

## Job Sources

| Source | Type | Confidence | Notes |
| --- | --- | --- | --- |
| Adzuna Jobs API | official API | `live_verified` | Real job API. Requires `MARKET_INTEL_ADZUNA_APP_ID` and `MARKET_INTEL_ADZUNA_APP_KEY`. Skips cleanly when keys are missing. |
| Arbeitnow Job API | public API | `live_verified` | Free no-key JSON API. Low-friction source for real postings. |
| Remotive Jobs API | public API | `live_verified` | Free remote-job JSON API. Useful for remote data/software roles. |
| `data/sample/curated_data_jobs.csv` | local CSV | `curated_demo` | Best source for clean dashboard screenshots and repeatable data-role descriptions. |
| Startup Data Jobs | local Python list | `curated_demo` | Small repeatable source for data startup roles. |
| Enterprise Analytics Jobs | local Python list | `curated_demo` | Small repeatable source for BI/cloud/governance roles. |
| Y Combinator Jobs | HTML scraper | `live_broad` | Optional legacy source. Real postings, but broad roles and more fragile than APIs. |
| RealPython Fake Jobs | HTML scraper | `test_source` | Good parser test page, but not a real job market source. |

## Course Sources

| Source | Type | Confidence | Notes |
| --- | --- | --- | --- |
| YouTube Learning | API or fallback | `fallback_learning` | Uses YouTube Data API when a key is set; otherwise local fallback rows. |
| Microsoft Learn | public API | `live_verified` | Good live source for Microsoft/cloud learning resources. |
| Open Course Catalog | local Python list | `curated_demo` | Free/open learning resources. |
| Vendor Docs Catalog | local Python list | `curated_demo` | Tool documentation and vendor training links. |
| University Open Catalog | local Python list | `curated_demo` | Statistics, ML, and visualization foundations. |

## Reference Sources

| Source | Type | Confidence | Notes |
| --- | --- | --- | --- |
| O*NET Online / O*NET-SOC | official occupational reference | `live_verified` | Used to ground skill taxonomy, SOC occupation mappings, wage medians, growth outlook, projected openings, and reference URLs. |
## Scraping Notes

The default `all` job mode now uses official APIs plus curated local job records. YC and RealPython remain available as optional modes for comparison and parser testing, but they are not the preferred source path.

Some large job and learning platforms restrict scraping or require authentication. For those, I would rather use an official API, public dataset, or manual export than scrape pages against their terms.

## GitHub practice issues

The practice recommender uses the official GitHub REST API. It first searches recently updated public repositories by an exact GitHub topic, then lists open issues labeled good first issue or help wanted. Pull requests are removed from the result.

Every returned row is labeled live_verified because it comes directly from GitHub's public API. This describes source provenance, not issue quality or suitability. Repository maintainers can close, relabel, or change issues at any time.

Unauthenticated access works for public data but has lower rate limits. Set MARKET_INTEL_GITHUB_TOKEN to use authenticated requests. Tokens are read from the environment and must never be committed.

Official references: https://docs.github.com/en/rest/search/search and https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
