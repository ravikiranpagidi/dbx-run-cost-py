from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class CostLineItem:
    sku_name: str | None = None
    cloud: str | None = None
    usage_unit: str | None = None
    currency_code: str | None = None
    dbus: float = 0.0
    cost: float = 0.0
    cluster_id: str | None = None
    warehouse_id: str | None = None
    records: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku_name": self.sku_name,
            "cloud": self.cloud,
            "usage_unit": self.usage_unit,
            "currency_code": self.currency_code,
            "dbus": self.dbus,
            "cost": self.cost,
            "cluster_id": self.cluster_id,
            "warehouse_id": self.warehouse_id,
            "records": self.records,
        }


@dataclass(frozen=True)
class CostReport:
    status: str
    source: str
    mode: str = "actual"
    report_created_at: str = field(default_factory=utc_now_iso)
    account_id: str | None = None
    workspace_id: str | None = None
    job_id: str | None = None
    job_run_id: str | None = None
    task_run_id: str | None = None
    job_name: str | None = None
    task_name: str | None = None
    run_date: str | None = None
    job_tag: str | None = None
    target_table: str | None = None
    output_table: str | None = None
    dbus: float = 0.0
    cost: float = 0.0
    currency_code: str = "USD"
    cloud: str | None = None
    sku_names: tuple[str, ...] = ()
    cluster_ids: tuple[str, ...] = ()
    warehouse_ids: tuple[str, ...] = ()
    usage_start_time: str | None = None
    usage_end_time: str | None = None
    usage_records: int = 0
    line_items: tuple[CostLineItem, ...] = ()
    query_latency_ms: int | None = None
    warnings: tuple[str, ...] = ()
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def not_found(
        cls,
        *,
        job_id: str | None = None,
        job_run_id: str | None = None,
        job_name: str | None = None,
        job_tag: str | None = None,
        target_table: str | None = None,
        warning: str | None = None,
    ) -> "CostReport":
        warnings = (warning,) if warning else ()
        return cls(
            status="not_found",
            source="system.billing.usage",
            job_id=job_id,
            job_run_id=job_run_id,
            job_name=job_name,
            job_tag=job_tag,
            target_table=target_table,
            warnings=warnings,
        )

    @classmethod
    def error_report(
        cls,
        *,
        error: str,
        job_id: str | None = None,
        job_run_id: str | None = None,
        job_name: str | None = None,
        job_tag: str | None = None,
        target_table: str | None = None,
    ) -> "CostReport":
        return cls(
            status="error",
            source="system.billing.usage",
            job_id=job_id,
            job_run_id=job_run_id,
            job_name=job_name,
            job_tag=job_tag,
            target_table=target_table,
            error=error,
            warnings=(error,),
        )

    @classmethod
    def estimated(
        cls,
        *,
        dbus: float,
        cost: float,
        currency_code: str = "USD",
        job_id: str | None = None,
        job_run_id: str | None = None,
        job_name: str | None = None,
        job_tag: str | None = None,
        target_table: str | None = None,
        warning: str = "estimated value, not reconciled with Databricks billing tables",
    ) -> "CostReport":
        return cls(
            status="estimated",
            source="manual_estimate",
            mode="estimate",
            job_id=job_id,
            job_run_id=job_run_id,
            job_name=job_name,
            job_tag=job_tag,
            target_table=target_table,
            dbus=float(dbus),
            cost=float(cost),
            currency_code=currency_code,
            warnings=(warning,),
        )

    @property
    def cost_usd(self) -> float:
        return self.cost if self.currency_code.upper() == "USD" else 0.0

    def with_output_table(self, table: str | None) -> "CostReport":
        return replace(self, output_table=table)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "source": self.source,
            "mode": self.mode,
            "report_created_at": self.report_created_at,
            "account_id": self.account_id,
            "workspace_id": self.workspace_id,
            "job_id": self.job_id,
            "job_run_id": self.job_run_id,
            "task_run_id": self.task_run_id,
            "job_name": self.job_name,
            "task_name": self.task_name,
            "run_date": self.run_date,
            "job_tag": self.job_tag,
            "target_table": self.target_table,
            "output_table": self.output_table,
            "dbus": self.dbus,
            "cost": self.cost,
            "cost_usd": self.cost_usd,
            "currency_code": self.currency_code,
            "cloud": self.cloud,
            "sku_names": list(self.sku_names),
            "cluster_ids": list(self.cluster_ids),
            "warehouse_ids": list(self.warehouse_ids),
            "usage_start_time": self.usage_start_time,
            "usage_end_time": self.usage_end_time,
            "usage_records": self.usage_records,
            "line_items": [item.to_dict() for item in self.line_items],
            "query_latency_ms": self.query_latency_ms,
            "warnings": list(self.warnings),
            "error": self.error,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, default=str)

    def to_table_row(self) -> dict[str, Any]:
        payload = self.to_dict()
        return {
            "report_created_at": self.report_created_at,
            "status": self.status,
            "source": self.source,
            "mode": self.mode,
            "account_id": self.account_id,
            "workspace_id": self.workspace_id,
            "job_id": self.job_id,
            "job_run_id": self.job_run_id,
            "task_run_id": self.task_run_id,
            "job_name": self.job_name,
            "task_name": self.task_name,
            "run_date": self.run_date,
            "job_tag": self.job_tag,
            "target_table": self.target_table,
            "output_table": self.output_table,
            "dbus": float(self.dbus),
            "cost": float(self.cost),
            "cost_usd": float(self.cost_usd),
            "currency_code": self.currency_code,
            "cloud": self.cloud,
            "sku_names_json": json.dumps(list(self.sku_names), sort_keys=True),
            "cluster_ids_json": json.dumps(list(self.cluster_ids), sort_keys=True),
            "warehouse_ids_json": json.dumps(list(self.warehouse_ids), sort_keys=True),
            "usage_start_time": self.usage_start_time,
            "usage_end_time": self.usage_end_time,
            "usage_records": int(self.usage_records),
            "query_latency_ms": self.query_latency_ms,
            "warnings_json": json.dumps(list(self.warnings), sort_keys=True),
            "line_items_json": json.dumps([item.to_dict() for item in self.line_items], sort_keys=True),
            "payload_json": json.dumps(payload, sort_keys=True, default=str),
        }

    def summary(self) -> str:
        label = self.job_name or self.job_tag or self.job_id or "Databricks job"
        run = f"run {self.job_run_id}" if self.job_run_id else "current run"

        if self.status == "found":
            return (
                f"{label} {run}: {self.dbus:.4f} DBUs, "
                f"{self.currency_code} {self.cost:.4f} from {self.usage_records} billing record(s)."
            )
        if self.status == "estimated":
            return f"{label} {run}: estimated {self.dbus:.4f} DBUs, {self.currency_code} {self.cost:.4f}."
        if self.status == "not_found":
            return f"{label} {run}: no billing records found yet."
        if self.error:
            return f"{label} {run}: cost lookup failed: {self.error}"
        return f"{label} {run}: status={self.status}."
