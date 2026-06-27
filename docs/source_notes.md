# Source Notes

This project mixes live sources with local/sample sources. That is deliberate.

## Job Sources

| Source | Type | Notes |
| --- | --- | --- |
| `data/sample/curated_data_jobs.csv` | local CSV | Best source for clean dashboard screenshots. |
| Y Combinator Jobs | live HTML | Good for startup hiring signals, but broad. |
| RealPython Fake Jobs | live HTML | Good scraper test page, but not a real job market source. |
| Startup Data Jobs | local Python list | Small repeatable source for data startup roles. |
| Enterprise Analytics Jobs | local Python list | Small repeatable source for BI/cloud/governance roles. |

## Course Sources

| Source | Type | Notes |
| --- | --- | --- |
| YouTube Learning | API or fallback | Uses YouTube Data API when a key is set; otherwise local fallback rows. |
| Microsoft Learn | public API | Good live source for Microsoft/cloud learning resources. |
| Open Course Catalog | local Python list | Free/open learning resources. |
| Vendor Docs Catalog | local Python list | Tool documentation and vendor training links. |
| University Open Catalog | local Python list | Statistics, ML, and visualization foundations. |

## Scraping Notes

Some large job and learning platforms restrict scraping or require authentication. For those, I would rather use an official API, public dataset, or manual export than scrape pages against their terms.
