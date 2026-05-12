from __future__ import annotations

import json
import time
from typing import Any

from .context import RunContext, resolve_context
from .databricks import get_active_spark_session, row_to_dict
from .exceptions import MissingSparkSession
from .models import CostLineItem, CostReport
from .sql import build_job_run_cost_sql
from .writers import write_delta_report


def report_current_run(
    *,
    spark: Any = None,
    dbutils: Any = None,
    context: RunContext | None = None,
    job_id: str | None = None,
    job_run_id: str | None = None,
    task_run_id: str | None = None,
    workspace_id: str | None = None,
    job_name: str | None = None,
    task_name: str | None = None,
    run_date: str | None = None,
    job_tag: str | None = None,
    target_table: str | None = None,
    write_table: str | None = None,
    write_path: str | None = None,
    lookback_days: int = 7,
    wait_seconds: int = 0,
    poll_seconds: int = 30,
    raise_on_error: bool = False,
) -> CostReport:
    resolved = context or resolve_context(dbutils=dbutils)
    resolved = resolved.with_overrides(
        job_id=job_id,
        job_run_id=job_run_id,
        task_run_id=task_run_id,
        workspace_id=workspace_id,
        job_name=job_name,
        task_name=task_name,
        run_date=run_date,
        job_tag=job_tag,
        target_table=target_table,
    )

    if not resolved.job_id or not resolved.job_run_id:
        report = CostReport.error_report(
            error="job_id and job_run_id are required; pass Databricks dynamic values as task parameters",
            job_id=resolved.job_id,
            job_run_id=resolved.job_run_id,
            job_name=resolved.job_name,
            job_tag=resolved.job_tag,
            target_table=resolved.target_table,
        )
        return _maybe_write(spark, report, write_table, write_path, raise_on_error)

    spark = spark or get_active_spark_session()
    if spark is None:
        error = "Spark session is required for billing-table lookup"
        if raise_on_error:
            raise MissingSparkSession(error)
        report = CostReport.error_report(
            error=error,
            job_id=resolved.job_id,
            job_run_id=resolved.job_run_id,
            job_name=resolved.job_name,
            job_tag=resolved.job_tag,
            target_table=resolved.target_table,
        )
        return _maybe_write(spark, report, write_table, write_path, raise_on_error)

    deadline = time.monotonic() + max(0, int(wait_seconds))
    first = True
    last_report: CostReport | None = None

    while first or time.monotonic() < deadline:
        first = False
        last_report = _query_once(spark=spark, context=resolved, lookback_days=lookback_days, raise_on_error=raise_on_error)
        if last_report.status == "found":
            return _maybe_write(spark, last_report, write_table, write_path, raise_on_error)
        if wait_seconds <= 0:
            break
        time.sleep(max(1, int(poll_seconds)))

    if last_report is None:
        last_report = CostReport.not_found(
            job_id=resolved.job_id,
            job_run_id=resolved.job_run_id,
            job_name=resolved.job_name,
            job_tag=resolved.job_tag,
            target_table=resolved.target_table,
            warning="no billing records found",
        )

    return _maybe_write(spark, last_report, write_table, write_path, raise_on_error)


def print_current_run_cost(**kwargs: Any) -> CostReport:
    report = report_current_run(**kwargs)
    print(report.summary())
    return report


def _query_once(*, spark: Any, context: RunContext, lookback_days: int, raise_on_error: bool) -> CostReport:
    started = time.monotonic()
    sql = build_job_run_cost_sql(
        job_id=context.job_id or "",
        job_run_id=context.job_run_id or "",
        workspace_id=context.workspace_id,
        start_date=context.normalized_run_date(),
        lookback_days=lookback_days,
    )

    try:
        rows = spark.sql(sql).collect()
    except Exception as exc:
        if raise_on_error:
            raise
        return CostReport.error_report(
            error=str(exc),
            job_id=context.job_id,
            job_run_id=context.job_run_id,
            job_name=context.job_name,
            job_tag=context.job_tag,
            target_table=context.target_table,
        )

    latency_ms = int((time.monotonic() - started) * 1000)
    data = row_to_dict(rows[0]) if rows else {}
    usage_records = int(_number(data.get("usage_records"), 0))

    if usage_records == 0:
        return CostReport.not_found(
            job_id=context.job_id,
            job_run_id=context.job_run_id,
            job_name=context.job_name,
            job_tag=context.job_tag,
            target_table=context.target_table,
            warning="billing records may not be available yet, or this run used all-purpose compute",
        ).with_output_table(None)

    line_items = _parse_line_items(data.get("line_items_json"))
    warnings: list[str] = []
    if float(_number(data.get("cost"), 0.0)) == 0.0 and float(_number(data.get("dbus"), 0.0)) > 0.0:
        warnings.append("DBUs were found but price lookup returned zero cost")

    return CostReport(
        status="found",
        source="system.billing.usage+system.billing.list_prices",
        mode="actual",
        account_id=_text(data.get("account_id")),
        workspace_id=_text(data.get("workspace_id")) or context.workspace_id,
        job_id=_text(data.get("job_id")) or context.job_id,
        job_run_id=_text(data.get("job_run_id")) or context.job_run_id,
        task_run_id=context.task_run_id,
        job_name=context.job_name or _text(data.get("job_name")),
        task_name=context.task_name,
        run_date=context.run_date,
        job_tag=context.job_tag,
        target_table=context.target_table,
        dbus=float(_number(data.get("dbus"), 0.0)),
        cost=float(_number(data.get("cost"), 0.0)),
        currency_code=_text(data.get("currency_code")) or "USD",
        cloud=_text(data.get("cloud")),
        sku_names=_string_tuple(data.get("sku_names")),
        cluster_ids=_string_tuple(data.get("cluster_ids")),
        warehouse_ids=_string_tuple(data.get("warehouse_ids")),
        usage_start_time=_text(data.get("usage_start_time")),
        usage_end_time=_text(data.get("usage_end_time")),
        usage_records=usage_records,
        line_items=line_items,
        query_latency_ms=latency_ms,
        warnings=tuple(warnings),
        metadata={"lookback_days": lookback_days},
    )


def _maybe_write(
    spark: Any,
    report: CostReport,
    write_table: str | None,
    write_path: str | None,
    raise_on_error: bool,
) -> CostReport:
    if not write_table and not write_path:
        return report
    if spark is None:
        if raise_on_error:
            raise MissingSparkSession("Spark session is required to write a Delta report")
        return report
    return write_delta_report(spark, report, table=write_table, path=write_path, raise_on_error=raise_on_error)


def _parse_line_items(value: Any) -> tuple[CostLineItem, ...]:
    if not value:
        return ()
    if isinstance(value, str):
        try:
            payload = json.loads(value)
        except json.JSONDecodeError:
            return ()
    else:
        payload = value
    if not isinstance(payload, list):
        return ()
    items: list[CostLineItem] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        items.append(
            CostLineItem(
                sku_name=_text(item.get("sku_name")),
                cloud=_text(item.get("cloud")),
                usage_unit=_text(item.get("usage_unit")),
                currency_code=_text(item.get("currency_code")),
                dbus=float(_number(item.get("dbus"), 0.0)),
                cost=float(_number(item.get("cost"), 0.0)),
                cluster_id=_text(item.get("cluster_id")),
                warehouse_id=_text(item.get("warehouse_id")),
                records=int(_number(item.get("records"), 0)),
            )
        )
    return tuple(items)


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _number(value: Any, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    try:
        return tuple(str(item) for item in value if item is not None and str(item))
    except TypeError:
        return (str(value),)
