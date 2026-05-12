from __future__ import annotations

import json
import unittest

from dbx_run_cost import report_current_run

from fakes import FakeSpark


class ReporterTests(unittest.TestCase):
    def test_report_current_run_returns_found_report(self) -> None:
        line_items = [
            {
                "sku_name": "JOBS_COMPUTE",
                "cloud": "AWS",
                "usage_unit": "DBU",
                "currency_code": "USD",
                "cluster_id": "abc",
                "warehouse_id": None,
                "dbus": 3.2,
                "cost": 0.64,
                "records": 2,
            }
        ]
        spark = FakeSpark(
            rows=[
                {
                    "account_id": "acct",
                    "workspace_id": "workspace",
                    "job_id": "123",
                    "job_run_id": "456",
                    "job_name": "orders",
                    "usage_start_time": "2026-05-11T00:00:00Z",
                    "usage_end_time": "2026-05-11T00:10:00Z",
                    "dbus": 3.2,
                    "cost": 0.64,
                    "currency_code": "USD",
                    "cloud": "AWS",
                    "usage_records": 2,
                    "sku_names": ["JOBS_COMPUTE"],
                    "cluster_ids": ["abc"],
                    "warehouse_ids": [],
                    "line_items_json": json.dumps(line_items),
                }
            ]
        )

        report = report_current_run(
            spark=spark,
            job_id="123",
            job_run_id="456",
            job_tag="daily_orders",
            target_table="prod.sales.orders",
        )

        self.assertEqual("found", report.status)
        self.assertEqual(3.2, report.dbus)
        self.assertEqual(0.64, report.cost)
        self.assertEqual(("abc",), report.cluster_ids)
        self.assertEqual("daily_orders", report.job_tag)
        self.assertEqual("prod.sales.orders", report.target_table)
        self.assertEqual(1, len(spark.queries))

    def test_report_current_run_returns_not_found_for_empty_billing(self) -> None:
        spark = FakeSpark(rows=[{"usage_records": 0}])

        report = report_current_run(spark=spark, job_id="123", job_run_id="456")

        self.assertEqual("not_found", report.status)
        self.assertIn("billing records", report.warnings[0])

    def test_missing_spark_returns_error_report(self) -> None:
        report = report_current_run(spark=None, job_id="123", job_run_id="456")

        self.assertEqual("error", report.status)
        self.assertIn("Spark session", report.error)

    def test_write_table_writes_one_row(self) -> None:
        spark = FakeSpark(rows=[{"usage_records": 0}])

        report = report_current_run(
            spark=spark,
            job_id="123",
            job_run_id="456",
            write_table="ops.job_run_costs",
        )

        self.assertEqual("ops.job_run_costs", report.output_table)
        self.assertEqual(1, len(spark.created))
        writer = spark.created[0].write
        self.assertEqual("delta", writer.format_name)
        self.assertEqual("append", writer.mode_name)
        self.assertEqual("ops.job_run_costs", writer.saved_table)
        self.assertEqual(1, len(spark.created[0].rows))


if __name__ == "__main__":
    unittest.main()
