# Methodology Notes

These notes explain how SkillSync separates source types and how the dashboard scores skill opportunity. The goal is to be transparent about what the project can and cannot claim.

## What Counts As Live Data

Live data means the pipeline collected records from a public page or public API during the current run.

| Source | Label | Notes |
| --- | --- | --- |
| Microsoft Learn Catalog | `live_verified` | Public Microsoft Learn catalog API. Good for learning-resource coverage, especially Microsoft/cloud topics. |
| Adzuna Jobs API | `live_verified` | Official job API. Requires free API credentials and skips cleanly when credentials are missing. |
| Arbeitnow Job API | `live_verified` | Public no-key JSON job API. |
| Remotive Jobs API | `live_verified` | Public no-key remote-jobs JSON API. |
| Y Combinator Jobs | `live_broad` | Optional legacy HTML scraper. Useful for comparison, but broad and more fragile than APIs. |
| YouTube Learning | `fallback_learning` | Uses the YouTube Data API when an API key is configured. Without a key, the connector uses local fallback learning rows. |

Live does not automatically mean perfect. Live sources can change HTML, include noisy roles, rate-limit requests, or return uneven coverage by skill.

## What Counts As Curated Data

Curated data means the project uses local records that were intentionally shaped for repeatable analysis, screenshots, and data-role examples.

| Source | Label | Notes |
| --- | --- | --- |
| `data/sample/curated_data_jobs.csv` | `curated_demo` | Clean data-role postings with full descriptions for reliable portfolio demos. |
| Startup Data Jobs | `curated_demo` | Small local feed for startup-style data roles. |
| Enterprise Analytics Jobs | `curated_demo` | Small local feed for BI, cloud, governance, and analytics roles. |
| Open Course Catalog | `curated_demo` | Maintained learning links from open/free learning resources. |
| Vendor Docs Catalog | `curated_demo` | Tool documentation and vendor training links. |
| University Open Catalog | `curated_demo` | Open learning resources for statistics, ML, and visualization foundations. |

Curated records are not a market sample by themselves. They are included so the project can run reliably after cloning and so the dashboard has clean examples for explanation.

## What Counts As Fake Or Test Data

Fake/test data is used for parser testing, smoke tests, and reliable local runs.

| Source | Label | Notes |
| --- | --- | --- |
| RealPython Fake Jobs | `test_source` | Public fake job board used to test HTML parsing. It is not a real labor-market source. |
| Seed Job Postings | `test_source` | Tiny local job sample used for fast offline pipeline checks. |
| Seed Course Listings | `fallback_learning` | Tiny local learning-resource sample used when running smoke tests. |

These records are useful for engineering reliability, but they should not be presented as real hiring demand.

## Source Confidence Labels

| Label | Meaning |
| --- | --- |
| `live_verified` | Live public source with a structured or reputable data endpoint. |
| `live_broad` | Live public source with real listings, but broad coverage or noisy job categories. |
| `curated_demo` | Local curated records designed for repeatable project demos and clear data-role examples. |
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
- Personal data such as recruiter names, emails, phone numbers, or applicant information.
- Claims about exact labor-market size, national demand, or salary benchmarks.

For those sources, the safer path would be an official API, licensed dataset, manual export, or clearly documented sample file.

## How Skills Are Extracted

Skill extraction is rule-based. The project scans job titles, job descriptions, course titles, subjects, roles, products, and platforms using maintained regex patterns in `src/etl/transform.py`.

This approach is simple and reproducible, but it has tradeoffs:

- It is easy to test and explain.
- It does not require paid NLP or LLM APIs.
- It can miss unusual synonyms or vague wording.
- It can over-count a skill if the source text is broad or repetitive.

## O*NET Skill And Wage Grounding

SkillSync maps tracked skills to related O*NET-SOC occupations when there is a reasonable data-career match. Those mappings add official occupation codes, occupation titles, annual median wage references, growth outlook, projected openings, and O*NET URLs to the skill summary table.

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
| `growth_score` | Uses O*NET occupation outlook when mapped; otherwise falls back to a maintained project signal. |
| `salary_premium_score` | Uses O*NET annual median wage references when mapped; otherwise falls back to posting salary ranges or a maintained project signal. |
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