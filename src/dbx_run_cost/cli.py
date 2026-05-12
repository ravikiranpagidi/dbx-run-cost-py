from __future__ import annotations

import argparse
import json

from .databricks import get_active_spark_session
from .reporter import report_current_run
from .sql import build_job_run_cost_sql


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dbx-run-cost", description="Databricks job run cost reporter.")
    subparsers = parser.add_subparsers(dest="command")

    report = subparsers.add_parser("report", help="query cost for a job run")
    report.add_argument("--job-id", required=True)
    report.add_argument("--job-run-id", required=True)
    report.add_argument("--workspace-id")
    report.add_argument("--job-name")
    report.add_argument("--job-tag")
    report.add_argument("--target-table")
    report.add_argument("--write-table")
    report.add_argument("--lookback-days", type=int, default=7)
    report.add_argument("--wait-seconds", type=int, default=0)
    report.add_argument("--format", choices=("text", "json"), default="text")

    sql = subparsers.add_parser("sql", help="print the billing query")
    sql.add_argument("--job-id", required=True)
    sql.add_argument("--job-run-id", required=True)
    sql.add_argument("--workspace-id")
    sql.add_argument("--lookback-days", type=int, default=7)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "sql":
        print(
            build_job_run_cost_sql(
                job_id=args.job_id,
                job_run_id=args.job_run_id,
                workspace_id=args.workspace_id,
                lookback_days=args.lookback_days,
            )
        )
        return 0

    if args.command == "report":
        spark = get_active_spark_session()
        report = report_current_run(
            spark=spark,
            job_id=args.job_id,
            job_run_id=args.job_run_id,
            workspace_id=args.workspace_id,
            job_name=args.job_name,
            job_tag=args.job_tag,
            target_table=args.target_table,
            write_table=args.write_table,
            lookback_days=args.lookback_days,
            wait_seconds=args.wait_seconds,
        )
        if args.format == "json":
            print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        else:
            print(report.summary())
        return 1 if report.status == "error" else 0

    parser.print_help()
    return 2
