# Project Notes

These are the working notes behind a few project choices. I keep them here so the repo still makes sense after I come back to it later.

## Why There Are Sample Sources

The live sources are useful, but they are not equally clean.

- RealPython Fake Jobs is stable and easy to scrape, but many rows are not data jobs.
- Y Combinator Jobs gives current startup roles, but many postings are software engineering roles rather than analytics or data engineering roles.
- The curated job CSV gives cleaner data-role descriptions, so it is better for screenshots, demos, and repeatable tests.

That is why the project keeps both live sources and sample/local sources.

## Why Skill Extraction Is Rule-Based

The skill extractor is intentionally simple. It uses a maintained list of regex patterns instead of an NLP model.

Reasons:

- It is easy to explain in an interview.
- It is reproducible when someone clones the repo.
- It avoids API keys or model costs.
- It is easier to test with small examples.

The tradeoff is that synonyms and vague wording can be missed.

## Why The Opportunity Index Uses Hand-Maintained Scores

The project does not have months of history yet, so growth and saturation cannot be fully calculated from the data. For now, those fields use simple maintained assumptions in `src/etl/transform.py`.

Once there are enough scheduled runs, the growth score could be replaced with a real week-over-week or month-over-month trend calculation.

## What I Would Improve Next

- Filter Y Combinator jobs more aggressively for data-related titles.
- Add a small role classifier for Analyst, Engineer, Scientist, and BI roles.
- Add a Docker-based CI check for PostgreSQL loading.
- Add parser tests whenever a new source is added.
- Replace the hand-maintained growth score once there are enough historical runs.
