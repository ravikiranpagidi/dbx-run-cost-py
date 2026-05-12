from __future__ import annotations

from typing import Any

from .models import CostReport


def write_delta_report(
    spark: Any,
    report: CostReport,
    *,
    table: str | None = None,
    path: str | None = None,
    mode: str = "append",
    merge_schema: bool = True,
    raise_on_error: bool = False,
) -> CostReport:
    if not table and not path:
        raise ValueError("table or path is required")

    row_report = report.with_output_table(table or path)
    row = row_report.to_table_row()

    try:
        writer = spark.createDataFrame([row]).write.format("delta").mode(mode)
        if merge_schema:
            writer = writer.option("mergeSchema", "true")
        if table:
            writer.saveAsTable(table)
        else:
            writer.save(path)
    except Exception:
        if raise_on_error:
            raise
        return report

    return row_report
