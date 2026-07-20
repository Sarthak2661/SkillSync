# Source Notes

SkillSync uses official APIs for current records and curated local data for repeatable demos and tests.

## Job Sources

| Source | Type | Confidence | Notes |
| --- | --- | --- | --- |
| Adzuna Jobs API | official API | `live_verified` | Real job API. Requires `MARKET_INTEL_ADZUNA_APP_ID` and `MARKET_INTEL_ADZUNA_APP_KEY`. Skips cleanly when keys are missing. |
| Arbeitnow Job API | public API | `live_verified` | Free no-key JSON API. Low-friction source for real postings. |
| Remotive Jobs API | public API | `live_verified` | Free remote-job JSON API. Useful for remote data/software roles; Remotive recommends polling only a few times per day. |
| HN Who's Hiring via Algolia | public API | `live_broad` | No-key official read API. Keeps top-level comments with technology-role signals from the latest monthly hiring thread. |
| `data/sample/curated_data_jobs.csv` | local CSV | `curated_demo` | Repeatable data and analytics role descriptions. |
| `data/sample/curated_technology_jobs.csv` | local CSV | `curated_demo` | Repeatable software, AI/ML, cloud, database, IT/security, and consulting descriptions. |
| Startup Data Jobs | local Python list | `curated_demo` | Small repeatable source for data startup roles. |
| Enterprise Analytics Jobs | local Python list | `curated_demo` | Small repeatable source for BI/cloud/governance roles. |

## Course Sources

| Source | Type | Confidence | Notes |
| --- | --- | --- | --- |
| YouTube Learning | API or fallback | `fallback_learning` | Uses YouTube Data API when a key is set; otherwise local fallback rows. |
| Microsoft Learn | public API | `live_verified` | Good live source for Microsoft/cloud learning resources. |
| freeCodeCamp Curriculum | GitHub Contents API | `live_verified` | Reads the official structured certification index from `freeCodeCamp/freeCodeCamp`; no README scraping. |
| GitHub Learning Paths | GitHub Repository Search API | `live_broad` | Finds recently maintained awesome lists and roadmaps for tracked technology skills. Repository metadata is used; README content is not ingested. |
| Open Course Catalog | local Python list | `curated_demo` | Free/open learning resources. |
| Official Learning Catalog | local verified catalog | `curated_demo` | Repeatable links to official data, software, AI/ML, cloud, database, security, testing, and IT learning pages. |
| Vendor Docs Catalog | local Python list | `curated_demo` | Tool documentation and vendor training links. |
| University Open Catalog | local Python list | `curated_demo` | Statistics, ML, and visualization foundations. |

Coursera and Udemy are not ingested because neither provides a suitable free public catalog API for this project. Khan Academy is also excluded because its public API is deprecated. The project does not replace these with third-party scraping services.

## Certification Sources

| Source | Type | Confidence | Notes |
| --- | --- | --- | --- |
| Credential Engine Registry | official CTDL Search API | `live_verified` | Optional real-time credential search. Requires an approved Credential Engine account and `MARKET_INTEL_CREDENTIAL_ENGINE_API_KEY`; not used for bulk downloading. |
| freeCodeCamp Certifications | GitHub Contents API or local snapshot | `live_verified` / `curated_demo` | Live modes verify selected technology certification files in the official curriculum repository. Default mode uses a repeatable snapshot. |
| Cloud and infrastructure catalog | maintained local JSON | `curated_demo` | AWS, Microsoft, Google Cloud, Linux Foundation, HashiCorp, Red Hat, and Cisco credentials, reviewed manually every few months. |

## Reference Sources

| Source | Type | Confidence | Notes |
| --- | --- | --- | --- |
| O*NET Online / O*NET-SOC | official occupational reference | `live_verified` | Used to ground skill taxonomy, SOC occupation mappings, wage medians, growth outlook, projected openings, and reference URLs. |
## Job Collection Notes

The live job path uses documented JSON APIs from Adzuna, Arbeitnow, Remotive, and HN Algolia. It does not scrape job-board HTML. The default `curated` mode remains local and repeatable; `job_apis` enables the four live connectors.

The default local scheduler and Airflow DAG run once per day. This keeps the trend history useful while avoiding unnecessary requests to live connectors. If you change the cadence for `job_apis` or `all`, review each provider's polling guidance first.

Some large job and learning platforms restrict scraping or require authentication. For those, I would rather use an official API, public dataset, or manual export than scrape pages against their terms.

The GitHub learning-path connector only accepts repository names containing `awesome` or `roadmap`, requires a minimum star count and recent activity, and stores generated descriptions instead of arbitrary README text. This keeps the source useful without treating community curation as an official curriculum.

## GitHub practice issues

The practice recommender uses the official GitHub REST API. It first searches recently updated public repositories by an exact GitHub topic, then lists open issues labeled good first issue or help wanted. Pull requests are removed from the result.

Every returned row is labeled live_verified because it comes directly from GitHub's public API. This describes source provenance, not issue quality or suitability. Repository maintainers can close, relabel, or change issues at any time.

Unauthenticated access works for public data but has lower rate limits. Set MARKET_INTEL_GITHUB_TOKEN to use authenticated requests. Tokens are read from the environment and must never be committed.

Official references: https://docs.github.com/en/rest/search/search and https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
