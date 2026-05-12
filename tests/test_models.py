from __future__ import annotations

import json
import unittest

from dbx_run_cost import CostReport, estimate_from_duration


class ModelTests(unittest.TestCase):
    def test_report_dict_and_table_row_are_plain_values(self) -> None:
        report = CostReport.estimated(
            job_id="123",
            job_run_id="456",
            dbus=2.5,
            cost=0.75,
            job_tag="daily_orders",
            target_table="prod.sales.orders",
        )

        payload = report.to_dict()
        row = report.to_table_row()

        self.assertEqual("estimated", payload["status"])
        self.assertEqual(0.75, payload["cost_usd"])
        self.assertEqual("daily_orders", row["job_tag"])
        self.assertEqual("prod.sales.orders", row["target_table"])
        self.assertTrue(json.loads(row["payload_json"]))

    def test_summary_is_readable(self) -> None:
        report = CostReport.estimated(job_name="orders", job_run_id="456", dbus=2, cost=1)

        self.assertIn("orders run 456", report.summary())
        self.assertIn("estimated", report.summary())

    def test_estimate_from_duration(self) -> None:
        report = estimate_from_duration(duration_seconds=1800, dbus_per_hour=10, price_per_dbu=0.2)

        self.assertEqual(5.0, report.dbus)
        self.assertEqual(1.0, report.cost)


if __name__ == "__main__":
    unittest.main()
