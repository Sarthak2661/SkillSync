# Methodology Notes

These notes explain how SkillSync separates source types and how the dashboard scores skill opportunity. The goal is to be transparent about what the project can and cannot claim.

## What Counts As Live Data

Live data means the pipeline collected records from a public page or public API during the current run.

| Source | Label | Notes |
| --- | --- | --- |
| Microsoft Learn Catalog | `live_verified` | Public Microsoft Learn catalog API. Good for learning-resource coverage, especially Microsoft/cloud topics. |
| freeCodeCamp Curriculum | `live_verified` | Official GitHub curriculum index. Only known technology certification files are normalized. |
| GitHub Learning Paths | `live_broad` | Official GitHub API results for maintained awesome lists and roadmaps. Community curation can still be uneven. |
| Credential Engine Registry | `live_verified` | Optional CTDL credential search when an approved API key is configured. |
| Adzuna Jobs API | `live_verified` | Official job API. Requires free API credentials and skips cleanly when credentials are missing. |
| Arbeitnow Job API | `live_verified` | Public no-key JSON job API. |
| Remotive Jobs API | `live_verified` | Public no-key remote-jobs JSON API. |
| HN Who's Hiring via Algolia | `live_broad` | Official no-key read API for user-authored posts in the latest monthly hiring thread. Only top-level technology-role posts are retained. |
| YouTube Learning | `fallback_learning` | Uses the YouTube Data API when an API key is configured. Without a key, the connector uses local fallback learning rows. It is excluded from the Live sources only dashboard view because the same connector can return fallback data. |

Live does not automatically mean perfect. Live sources can change HTML, include noisy roles, rate-limit requests, or return uneven coverage by skill.

## What Counts As Curated Data

Curated data means the project uses local records intentionally shaped for repeatable analysis, screenshots, and role examples.

| Source | Label | Notes |
| --- | --- | --- |
| `data/sample/curated_data_jobs.csv` | `curated_demo` | Clean data-role examples retained for repeatable comparisons. |
| `data/sample/curated_technology_jobs.csv` | `curated_demo` | Software, AI/ML, cloud, database, IT/security, and consulting examples with full descriptions. |
| Startup Data Jobs | `curated_demo` | Small local feed for startup-style data roles. |
| Enterprise Analytics Jobs | `curated_demo` | Small local feed for BI, cloud, governance, and analytics roles. |
| Open Course Catalog | `curated_demo` | Maintained learning links from open/free learning resources. |
| Official Learning Catalog | `curated_demo` | Verified official documentation and training links stored locally so the default run is broad but repeatable. |
| Vendor Docs Catalog | `curated_demo` | Tool documentation and vendor training links. |
| University Open Catalog | `curated_demo` | Open learning resources for statistics, ML, and visualization foundations. |
| Cloud Certification Catalog | `curated_demo` | Manually reviewed AWS, Microsoft, and Google Cloud credential pages stored as local JSON. |
| freeCodeCamp Certification Snapshot | `curated_demo` | Repeatable fallback used when live GitHub verification is not selected or unavailable. |

Curated records are not a market sample by themselves. They are included so the project can run reliably after cloning and so the dashboard has clean examples for explanation.

## What Counts As Fake Or Test Data

Fake/test data is used for parser testing, smoke tests, and reliable local runs.

| Source | Label | Notes |
| --- | --- | --- |
| Seed Job Postings | `test_source` | Tiny local job sample used for fast offline pipeline checks. |
| Seed Course Listings | `fallback_learning` | Tiny local learning-resource sample used when running smoke tests. |

These records are useful for engineering reliability, but they should not be presented as real hiring demand.

## Source Confidence Labels

| Label | Meaning |
| --- | --- |
| `live_verified` | Live public source with a structured or reputable data endpoint. |
| `live_broad` | Live public source with real listings, but broad coverage or noisy job categories. |
| `curated_demo` | Local curated records designed for repeatable project demos and clear technology-role examples. |
| `fallback_learning` | Learning records that may come from an API when configured, or fallback rows when no key is available. |
| `test_source` | Fake, sample, or parser-test data that should not be treated as market evidence. |

The dashboard source-scope filter uses these ideas to separate demo-safe data, live sources, curated market snapshots, and all sources.

## What Is Excluded

The project intentionally excludes sources that are likely to require authentication, paid access, or terms-sensitive scraping.

Examples:

- LinkedIn job pages and LinkedIn Learning pages.
- Indeed, Naukri, or other job boards without an approved API or export path.
- Handshake pages behind login.
- Paid course catalogs that do not expose a public API.
- Coursera and Udemy catalog scraping, including paid third-party scraper services.
- Khan Academy's deprecated public API.
- Personal data such as recruiter names, emails, phone numbers, or applicant information.
- Claims about exact labor-market size, national demand, or salary benchmarks.

For those sources, the safer path would be an official API, licensed dataset, manual export, or clearly documented sample file.

## How Skills Are Extracted

Skill extraction is rule-based. The project scans job titles, descriptions, course metadata, roles, products, and platforms using the taxonomy in `src/domain/technology.py` and the ETL rules in `src/etl/transform.py`.

## Role Families

Every job is assigned a standardized role and one of eight families: Data & Analytics, Software Engineering, AI & Machine Learning, Cloud & Platform, Database, IT & Security, Technology Consulting, or Other Technology. The same family labels flow into course coverage, certification recommendations, API filters, dbt models, and Power BI dimensions.

This approach is simple and reproducible, but it has tradeoffs:

- It is easy to test and explain.
- It does not require paid NLP or LLM APIs.
- It can miss unusual synonyms or vague wording.
- It can over-count a skill if the source text is broad or repetitive.

## O*NET Skill And Wage Grounding

SkillSync maps tracked skills to related O*NET-SOC occupations when there is a defensible occupation match. Those mappings add official occupation codes, occupation titles, annual median wage references, growth outlook, projected openings, and O*NET URLs to the skill summary table.

This does not mean O*NET has a perfect one-to-one record for every tool. O*NET describes occupations, not every library or vendor product. For example, Python can map cleanly to Data Scientists and Software Developers, while a tool such as dbt is mapped through related analytics and database occupations. When a skill does not have a confident mapping, the project falls back to the local market-signal table and labels it as a project fallback.
## How The Skill Opportunity Index Is Calculated

The main score is the Skill Opportunity Index, scaled from 0 to 100.

```text
Skill Opportunity Index =
50
+ 0.35 * demand_score
+ 0.25 * growth_score
+ 0.25 * salary_premium_score
- 0.20 * course_supply_score
- 0.15 * saturation_score
```

Inputs:

| Input | Meaning |
| --- | --- |
| `demand_score` | Normalized job demand for the selected run or dashboard source view. |
| `course_supply_score` | Normalized course/resource supply for the selected run or source view. |
| Growth score | Numeric BLS employment projection for mapped occupations; maintained fallback otherwise. |
| Salary premium score | BLS median wage for mapped occupations; posting salary or maintained fallback otherwise. |
| `saturation_score` | Maintained signal for whether a skill is crowded, basic, or more specialized. |

Labels:

| Opportunity label | Score range | Interpretation |
| --- | --- | --- |
| `High-value` | 75-100 | Strong learning or portfolio signal. |
| `Good bet` | 60-74 | Useful skill with market relevance. |
| `Balanced` | 45-59 | Useful, but not clearly under-supplied. |
| `Lower priority` | 0-44 | Lower demand, high supply, or weaker signal. |

## How To Interpret The Score

The score is a prioritization aid, not a real labor-market forecast. It is best used to compare skills inside the same run and source scope.

Good use:

- Compare Python vs SQL vs Airflow inside the current dashboard run.
- See whether a skill appears more job-heavy or course-heavy.
- Identify skills worth exploring in the Skills Explorer or Learning & Certification Path pages.

Avoid overclaiming:

- Do not say the score proves national demand.
- Do not compare it directly with external labor-market reports.
- Do not treat fake/test sources as real market evidence.
- Do not claim precise wage premium for a specific employer or city; O*NET is an occupational benchmark, not a live compensation offer.

The dashboard includes source filters and quality checks so these caveats are visible instead of hidden.

## Certification Recommendation Method

Certification rows come from the maintained cloud catalog, freeCodeCamp curriculum records, and optionally Credential Engine. Each row keeps its source name, source-confidence label, and last verification date. The recommendation score combines the catalog's base priority with the current Skill Opportunity Index:

```text
recommendation_score = 0.55 * priority_score + 0.45 * opportunity_index
```

Credential Engine is queried only for a small relevant result set. Its Search API requires account approval and is not intended for bulk scraping. Certification prices marked as unavailable should be checked on the provider's page because Microsoft and other providers can vary pricing by region.

## O*NET and BLS reference data

SkillSync's tracked labels are a project-defined extraction taxonomy, not the complete O*NET taxonomy.

An exact technology match in the O*NET Software Skills file receives the evidence status software_skill_verified and retains the official workplace-example label. Broader concepts such as ETL, data quality, and responsible AI receive occupation_mapping_only. Those links are documented project mappings, not exact O*NET software-skill assertions.

O*NET supplies occupation codes and software-skill evidence. BLS supplies wages and numeric employment projections. Refresh the compact reference snapshot with:

    python scripts/refresh_onet_reference.py

O*NET data is licensed under CC BY 4.0. Attribution: O*NET 30.3 Database, U.S. Department of Labor, Employment and Training Administration. SkillSync filters and maps the source records.


## Practice recommendation method

Practice recommendations are live operational suggestions, not part of the Skill Opportunity Index. The recommender searches public repositories with an exact GitHub topic and recent code activity, ranks established repositories by stars, and retrieves open issues labeled good first issue or help wanted. Pull requests are excluded.

The repository topic provides the skill connection. The issue label indicates maintainer intent, but it does not prove that the issue is easy, unclaimed, or still appropriate for a new contributor. Users should read the repository contribution guide and issue discussion before starting work.
