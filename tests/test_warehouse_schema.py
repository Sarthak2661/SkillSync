from __future__ import annotations

import unittest

from src.warehouse.postgres import DDL_STATEMENTS


class WarehouseSchemaTests(unittest.TestCase):
    def test_skill_trend_role_family_precedes_table_constraints(self) -> None:
        statement = next(
            sql for sql in DDL_STATEMENTS
            if "CREATE TABLE IF NOT EXISTS market_intel.skill_trend_history" in sql
        )

        role_family_position = statement.index("role_family TEXT")
        loaded_at_position = statement.index("loaded_at TIMESTAMPTZ")
        primary_key_position = statement.index("PRIMARY KEY")

        self.assertLess(role_family_position, loaded_at_position)
        self.assertLess(loaded_at_position, primary_key_position)
        self.assertNotIn("PRIMARY KEY (run_id, source_name, skill, location, role_category)\n        role_family", statement)


if __name__ == "__main__":
    unittest.main()
