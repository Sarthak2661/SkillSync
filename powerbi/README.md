# Power BI Star Schema

Run python pipeline.py, then python export_powerbi.py. Import the CSV files from powerbi/export.

Use the three facts, five dimensions, and three marts as the reporting model. fact_jobs and fact_courses remain available for drill-through detail.

## Relationships

Create one-to-many, single-direction relationships from dimensions to facts:

| Dimension | Key | Fact or mart |
|---|---|---|
| dim_skill | skill_key | All three facts and all three marts |
| dim_role | role_key | Job mentions, trend history, role demand, readiness |
| dim_location | location_key | Job mentions and trend history |
| dim_source | source_key | All three facts |
| dim_time | time_key | All three facts and role demand |

Do not create direct fact-to-fact relationships.

## Core DAX measures

    Skill Demand Score =
    VAR Mentions = SUM(fact_job_skill_mentions[mention_count])
    VAR MaximumSkillMentions =
        MAXX(ALL(dim_skill[skill]), CALCULATE(SUM(fact_job_skill_mentions[mention_count])))
    RETURN ROUND(100 * DIVIDE(Mentions, MaximumSkillMentions, 0), 0)

    Skill Supply Score =
    VAR Coverage = SUM(fact_course_skill_coverage[coverage_count])
    VAR MaximumSkillCoverage =
        MAXX(ALL(dim_skill[skill]), CALCULATE(SUM(fact_course_skill_coverage[coverage_count])))
    RETURN ROUND(100 * DIVIDE(Coverage, MaximumSkillCoverage, 0), 0)

    Opportunity Index =
    AVERAGE(mart_skill_opportunity[opportunity_index])

    High-Confidence Demand Only =
    CALCULATE(
        SUM(fact_job_skill_mentions[mention_count]),
        fact_job_skill_mentions[high_confidence_demand] = 1
    )

    Rising Skills Count =
    VAR CurrentRun = MAX(dim_time[run_timestamp])
    VAR PreviousRun =
        MAXX(FILTER(ALL(dim_time), dim_time[run_timestamp] < CurrentRun), dim_time[run_timestamp])
    RETURN
    COUNTROWS(
        FILTER(
            VALUES(dim_skill[skill_key]),
            VAR CurrentDemand =
                CALCULATE(SUM(fact_skill_trend_history[job_count]), dim_time[run_timestamp] = CurrentRun)
            VAR PreviousDemand =
                CALCULATE(SUM(fact_skill_trend_history[job_count]), dim_time[run_timestamp] = PreviousRun)
            RETURN CurrentDemand > PreviousDemand
        )
    )

## Suggested pages

1. Market Overview: demand, supply, opportunity index, high-confidence demand, and rising skills.
2. Role Demand: role-by-skill matrix from mart_role_skill_demand.
3. Learning Readiness: readiness gap from mart_role_readiness_inputs.
4. Trend History: skill demand over dim_time[run_timestamp].
5. Methodology and Quality: source confidence, O*NET evidence, and quality results.

## dbt commands

    docker compose --profile analytics run --rm dbt build
    docker compose --profile analytics run --rm dbt docs generate
    docker compose --profile analytics run --rm -p 8081:8080 dbt docs serve --host 0.0.0.0 --port 8080

Open http://127.0.0.1:8081 for generated model documentation and interactive lineage.
