from __future__ import annotations

import unittest

from dbx_run_cost.sql import build_job_run_cost_sql, quote_sql


class SqlTests(unittest.TestCase):
    def test_quote_sql_escapes_single_quotes(self) -> None:
        self.assertEqual("'a''b'", quote_sql("a'b"))

    def test_cost_query_filters_job_run_and_workspace(self) -> None:
        sql = build_job_run_cost_sql(job_id="123", job_run_id="456", workspace_id="999")

        self.assertIn("usage.usage_metadata.job_id = '123'", sql)
        self.assertIn("usage.usage_metadata.job_run_id = '456'", sql)
        self.assertIn("usage.workspace_id = '999'", sql)
        self.assertIn("system.billing.usage", sql)
        self.assertIn("system.billing.list_prices", sql)

    def test_start_date_replaces_lookback_filter(self) -> None:
        sql = build_job_run_cost_sql(job_id="123", job_run_id="456", start_date="2026-05-11")

        self.assertIn("usage.usage_date >= DATE '2026-05-11'", sql)
        self.assertNotIn("date_sub(current_date()", sql)

    def test_requires_job_identifiers(self) -> None:
        with self.assertRaises(ValueError):
            build_job_run_cost_sql(job_id="", job_run_id="456")


if __name__ == "__main__":
    unittest.main()
