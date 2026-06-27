import unittest

from src.etl.transform import extract_skills, normalize_skill_text
from src.ingestion.course_sources import YouTubeLearningSource
from src.ingestion.job_sources import parse_realpython_fake_jobs, parse_ycombinator_jobs


class ParserTests(unittest.TestCase):
    def test_parse_realpython_fake_jobs_card(self):
        html = """
        <div class="card-content">
          <h2 class="title">Data Engineer</h2>
          <h3 class="company">Example Analytics</h3>
          <p class="location">Remote</p>
          <time>2026-06-20</time>
          <footer>
            <a href="/apply">Apply</a>
            <a href="/jobs/data-engineer">Details</a>
          </footer>
        </div>
        """

        jobs = parse_realpython_fake_jobs(html, "https://example.com")

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].title, "Data Engineer")
        self.assertEqual(jobs[0].company, "Example Analytics")
        self.assertEqual(jobs[0].location, "Remote")
        self.assertEqual(jobs[0].url, "https://example.com/jobs/data-engineer")

    def test_parse_ycombinator_jobs_card(self):
        html = """
        <ul>
          <li>
            <a href="/companies/acme/jobs/abc123-data-engineer">Data Engineer</a>
            Acme AI (S24) • Full-time • $120K - $180K • San Francisco / Remote
          </li>
        </ul>
        """

        jobs = parse_ycombinator_jobs(html, "https://www.ycombinator.com/jobs")

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].title, "Data Engineer")
        self.assertEqual(jobs[0].company, "Acme AI")
        self.assertEqual(jobs[0].salary_min, 120000)
        self.assertEqual(jobs[0].salary_max, 180000)
        self.assertEqual(jobs[0].location, "San Francisco / Remote")
        self.assertEqual(
            jobs[0].url,
            "https://www.ycombinator.com/companies/acme/jobs/abc123-data-engineer",
        )

    def test_youtube_fallback_source_returns_learning_records(self):
        records = YouTubeLearningSource().fetch()

        self.assertGreaterEqual(len(records), 4)
        self.assertEqual(records[0].source_name, "youtube_learning")
        self.assertIn("youtube.com", records[0].payload["url"])


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

    def test_normalize_skill_text_handles_separators(self):
        normalized = normalize_skill_text("Power-BI / Azure_Data_Factory + SQL")

        self.assertEqual(normalized, "power bi azure data factory sql")


if __name__ == "__main__":
    unittest.main()
