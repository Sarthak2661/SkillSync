# Power BI Dashboard Package

This folder contains the Power BI handoff for SkillSync.

Run the ETL first:

```powershell
python pipeline.py
```

Then export Power BI-ready tables:

```powershell
python export_powerbi.py
```

The export writes CSV tables to `powerbi/export/`.

## Import Tables

In Power BI Desktop:

1. Select **Get Data > Text/CSV**.
2. Import every CSV in `powerbi/export/`.
3. Set relationships:
   - `dim_skill[skill]` one-to-many `fact_skill_gap[skill]`
   - `dim_skill[skill]` one-to-many `fact_skill_trend[skill]`
   - `dim_skill[skill]` one-to-many `bridge_job_skills[skill]`
   - `dim_skill[skill]` one-to-many `bridge_course_skills[skill]`
   - `fact_jobs[job_id]` one-to-many `bridge_job_skills[job_id]`
   - `fact_courses[course_id]` one-to-many `bridge_course_skills[course_id]`
   - `dim_company[company]` one-to-many `fact_jobs[company]`
   - `dim_platform[platform]` one-to-many `fact_courses[platform]`
   - `dim_skill[skill]` one-to-many `fact_certification_recommendations[skill]`

Use single-direction filtering from dimensions to facts/bridges.

## Core Measures

Create these DAX measures:

```DAX
Job Postings = COUNTROWS(fact_jobs)

Course Listings = COUNTROWS(fact_courses)

Unique Skills = DISTINCTCOUNT(dim_skill[skill])

Historical Runs = DISTINCTCOUNT(fact_skill_trend[run_id])

High Opportunity Skills =
CALCULATE(
    DISTINCTCOUNT(fact_skill_gap[skill]),
    fact_skill_gap[status] = "High opportunity"
)

High Value Skills =
CALCULATE(
    DISTINCTCOUNT(fact_skill_gap[skill]),
    fact_skill_gap[opportunity_label] = "High-value"
)

Average Opportunity Index = AVERAGE(fact_skill_gap[opportunity_index])

Average Gap Score = AVERAGE(fact_skill_gap[gap_score])

Trend Job Count = SUM(fact_skill_trend[job_count])

Trend Course Count = SUM(fact_skill_trend[course_count])

Average Skill Salary Min = AVERAGE(fact_skill_trend[salary_min_avg])

Average Skill Salary Max = AVERAGE(fact_skill_trend[salary_max_avg])

Quality Warnings =
CALCULATE(
    COUNTROWS(fact_quality_checks),
    fact_quality_checks[status] <> "pass"
)

Job Skill Coverage =
DIVIDE(
    CALCULATE(COUNTROWS(fact_jobs), fact_jobs[skill_count] > 0),
    COUNTROWS(fact_jobs)
)

Course Skill Coverage =
DIVIDE(
    CALCULATE(COUNTROWS(fact_courses), fact_courses[skill_count] > 0),
    COUNTROWS(fact_courses)
)

Certification Recommendations = COUNTROWS(fact_certification_recommendations)

Free Certifications =
CALCULATE(
    COUNTROWS(fact_certification_recommendations),
    fact_certification_recommendations[free_or_paid] = "Free"
)

Average Certification Recommendation Score =
AVERAGE(fact_certification_recommendations[recommendation_score])
```

## Dashboard Pages

### Page 1: Executive Overview

Cards:

- Job Postings
- Course Listings
- Unique Skills
- High Opportunity Skills
- High Value Skills
- Average Opportunity Index
- Historical Runs
- Quality Warnings

Charts:

- Bar chart: `dim_skill[skill]` by `fact_skill_gap[opportunity_index]`, sorted descending.
- Clustered bar: `dim_skill[category]` by job demand and course supply.
- Table: `fact_quality_checks[check_name]`, `status`, `severity`, `message`.

Filters:

- Skill category
- Gap status
- Run ID

### Page 2: Skill Gap Explorer

Charts:

- Scatter: `job_demand` vs `course_supply`, legend by `category`.
- Matrix: skill, category, opportunity index, opportunity label, job demand, course supply, growth score, salary premium score, saturation score.
- Bar chart: top high-opportunity skills.

Use conditional formatting on `opportunity_index`:

- 75 and above: high-value color
- 60 to 74: good-bet color
- 45 to 59: neutral color
- Below 45: lower-priority color

### Page 3: Jobs And Courses Detail

Tables:

- Job postings with title, company, location, remote type, skills, URL.
- Courses with title, platform, level, duration, skills, URL.

Filters:

- Skill
- Company
- Platform
- Remote type
- Level

### Page 4: Skill Trends

Charts:

- Line chart: `fact_skill_trend[run_timestamp]` by `Trend Job Count`, legend by `dim_skill[skill]`.
- Line chart: cloud comparison for AWS, Azure, and GCP.
- Line chart: BI comparison for Power BI and Tableau.
- Clustered column: `role_category` by `Trend Job Count`.
- Matrix: skill, source name, location, role category, job count, course count, average salary min, average salary max.

Filters:

- Skill
- Source name
- Location
- Role category
- Run timestamp

### Page 5: Data Quality

Cards:

- Quality Warnings
- Failed checks
- Warning checks

Charts:

- Bar chart: checks by status and severity.
- Table: dataset, check name, severity, failed count, message.

Add a text note:

> Trend claims should be interpreted with the quality checks and source coverage shown on this page.

### Page 6: Learning And Certification Path

Cards:

- Certification Recommendations
- Free Certifications
- Average Certification Recommendation Score

Tables:

- Certification recommendations with skill, certification name, provider, level, free/paid status, cost, target roles, opportunity index, and recommendation score.
- Related course resources from `fact_courses`, filtered by selected skill.

Filters:

- Skill
- Free or paid
- Provider

