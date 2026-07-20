import unittest

import pandas as pd

from src.analytics.onet_reference import onet_profile_for_skill, onet_salary_score
from src.etl.transform import build_skill_gap_summary, extract_skills, normalize_skill_text
from src.domain.technology import classify_role

class SkillExtractionTests(unittest.TestCase):
    def test_extracts_core_data_stack_skills(self):
        text = "Build Python ETL pipelines with SQL, Airflow, dbt, Power BI, and data quality checks."

        skills = extract_skills(text)

        self.assertIn("Python", skills)
        self.assertIn("SQL", skills)
        self.assertIn("ETL", skills)
        self.assertIn("Airflow", skills)
        self.assertIn("dbt", skills)
        self.assertIn("Power BI", skills)
        self.assertIn("Data Quality", skills)

    def test_extracts_cloud_and_modern_ai_skills(self):
        text = "Use Snowflake, AWS, LLMs, GenAI, and Responsible AI controls for analytics workflows."

        skills = extract_skills(text)

        self.assertIn("Snowflake", skills)
        self.assertIn("AWS", skills)
        self.assertIn("LLMs", skills)
        self.assertIn("GenAI", skills)
        self.assertIn("Responsible AI", skills)

    def test_normalize_skill_text_handles_separators(self):
        normalized = normalize_skill_text("Power-BI / Azure_Data_Factory + SQL")

        self.assertEqual(normalized, "power bi azure data factory sql")
    def test_extracts_broader_technology_stack_skills(self):
        text = (
            "Build Java and TypeScript services with React, Kubernetes, Terraform, MLflow, RAG, "
            "Oracle Database, ITIL, and Playwright."
        )

        skills = extract_skills(text)

        for expected in [
            "Java",
            "TypeScript",
            "React",
            "Kubernetes",
            "Terraform",
            "MLflow",
            "RAG",
            "Oracle Database",
            "ITIL",
            "Playwright",
        ]:
            self.assertIn(expected, skills)


class RoleTaxonomyTests(unittest.TestCase):
    def test_classifies_requested_technology_role_families(self):
        cases = {
            "Senior Backend Engineer": "Software Engineering",
            "MLOps Engineer": "AI & Machine Learning",
            "Cloud Platform Engineer": "Cloud & Platform",
            "Oracle DBA": "Database",
            "Cybersecurity Analyst": "IT & Security",
            "AI Strategy Consultant": "Technology Consulting",
            "Data Analyst": "Data & Analytics",
        }

        for title, expected_family in cases.items():
            with self.subTest(title=title):
                self.assertEqual(classify_role(title).role_family, expected_family)

class ScoringTests(unittest.TestCase):
    def test_skill_gap_summary_scores_filtered_inputs(self):
        jobs = pd.DataFrame(
            [
                {"skills": "Python|SQL", "salary_min": 100000, "salary_max": 140000},
                {"skills": "Python|Airflow", "salary_min": 120000, "salary_max": 160000},
                {"skills": "SQL", "salary_min": 80000, "salary_max": 110000},
            ]
        )
        courses = pd.DataFrame([{"skills": "SQL"}, {"skills": "Power BI"}])

        summary = build_skill_gap_summary(jobs, courses)
        python_row = summary[summary["skill"] == "Python"].iloc[0]
        sql_row = summary[summary["skill"] == "SQL"].iloc[0]

        self.assertEqual(int(python_row["job_demand"]), 2)
        self.assertEqual(int(python_row["course_supply"]), 0)
        self.assertGreaterEqual(int(python_row["opportunity_index"]), 60)
        self.assertEqual(int(sql_row["job_demand"]), 2)
        self.assertEqual(int(sql_row["course_supply"]), 1)


    def test_skill_gap_summary_includes_onet_reference_fields(self):
        jobs = pd.DataFrame(
            [
                {"skills": "Python|SQL", "salary_min": 90000, "salary_max": 120000},
                {"skills": "SQL", "salary_min": 95000, "salary_max": 125000},
            ]
        )
        courses = pd.DataFrame([{"skills": "SQL"}])

        summary = build_skill_gap_summary(jobs, courses)
        python_row = summary[summary["skill"] == "Python"].iloc[0]
        sql_row = summary[summary["skill"] == "SQL"].iloc[0]

        self.assertIn("15-2051.00", python_row["onet_soc_codes"])
        self.assertIn("Data Scientists", python_row["onet_occupations"])
        self.assertEqual(int(sql_row["salary_premium_score"]), onet_salary_score("SQL"))
        self.assertEqual(sql_row["taxonomy_source"], onet_profile_for_skill("SQL").taxonomy_source)
