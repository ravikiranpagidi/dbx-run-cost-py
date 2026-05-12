from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from datetime import date
from typing import Any


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "null"}:
        return None
    if "{{" in text and "}}" in text:
        return None
    return text


@dataclass(frozen=True)
class RunContext:
    job_id: str | None = None
    job_run_id: str | None = None
    task_run_id: str | None = None
    workspace_id: str | None = None
    job_name: str | None = None
    task_name: str | None = None
    run_date: str | None = None
    job_tag: str | None = None
    target_table: str | None = None
    source: str = "manual"
    metadata: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "RunContext":
        values = {
            "job_id": _first_env("DBX_COST_JOB_ID", "DATABRICKS_JOB_ID"),
            "job_run_id": _first_env("DBX_COST_JOB_RUN_ID", "DATABRICKS_JOB_RUN_ID"),
            "task_run_id": _first_env("DBX_COST_TASK_RUN_ID", "DATABRICKS_TASK_RUN_ID"),
            "workspace_id": _first_env("DBX_COST_WORKSPACE_ID", "DATABRICKS_WORKSPACE_ID"),
            "job_name": _first_env("DBX_COST_JOB_NAME", "DATABRICKS_JOB_NAME"),
            "task_name": _first_env("DBX_COST_TASK_NAME", "DATABRICKS_TASK_NAME"),
            "run_date": _first_env("DBX_COST_RUN_DATE", "DATABRICKS_JOB_RUN_DATE"),
            "job_tag": _first_env("DBX_COST_JOB_TAG"),
            "target_table": _first_env("DBX_COST_TARGET_TABLE"),
        }
        return cls(**values, source="env")

    @classmethod
    def from_widgets(cls, dbutils: Any) -> "RunContext":
        values = {
            "job_id": _widget(dbutils, "job_id"),
            "job_run_id": _widget(dbutils, "job_run_id"),
            "task_run_id": _widget(dbutils, "task_run_id"),
            "workspace_id": _widget(dbutils, "workspace_id"),
            "job_name": _widget(dbutils, "job_name"),
            "task_name": _widget(dbutils, "task_name"),
            "run_date": _widget(dbutils, "run_date"),
            "job_tag": _widget(dbutils, "dbx_cost_tag") or _widget(dbutils, "job_tag"),
            "target_table": _widget(dbutils, "dbx_cost_target_table") or _widget(dbutils, "target_table"),
        }
        return cls(**values, source="widgets")

    @classmethod
    def from_dbutils_tags(cls, dbutils: Any) -> "RunContext":
        tags = _dbutils_tags(dbutils)
        values = {
            "job_id": tags.get("jobId") or tags.get("job_id"),
            "job_run_id": tags.get("jobRunId") or tags.get("job_run_id"),
            "task_run_id": tags.get("taskRunId") or tags.get("task_run_id"),
            "workspace_id": tags.get("orgId") or tags.get("workspaceId") or tags.get("workspace_id"),
            "job_name": tags.get("jobName") or tags.get("job_name"),
            "task_name": tags.get("taskKey") or tags.get("task_name"),
        }
        return cls(**{key: _clean(value) for key, value in values.items()}, source="dbutils_tags", metadata=tags)

    def with_overrides(self, **overrides: Any) -> "RunContext":
        cleaned = {key: _clean(value) for key, value in overrides.items() if key in self.__dataclass_fields__}
        return replace(self, **{key: value for key, value in cleaned.items() if value is not None})

    def merged(self, other: "RunContext") -> "RunContext":
        data = self.__dict__.copy()
        for key, value in other.__dict__.items():
            if key == "metadata":
                data["metadata"] = {**self.metadata, **other.metadata}
            elif value:
                data[key] = value
        return RunContext(**data)

    def normalized_run_date(self) -> str | None:
        if not self.run_date:
            return None
        try:
            return date.fromisoformat(self.run_date[:10]).isoformat()
        except ValueError:
            return None


def resolve_context(dbutils: Any = None, **overrides: Any) -> RunContext:
    context = RunContext.from_env()

    if dbutils is not None:
        context = context.merged(RunContext.from_dbutils_tags(dbutils))
        context = context.merged(RunContext.from_widgets(dbutils))

    return context.with_overrides(**overrides)


def _first_env(*names: str) -> str | None:
    for name in names:
        value = _clean(os.environ.get(name))
        if value:
            return value
    return None


def _widget(dbutils: Any, name: str) -> str | None:
    try:
        return _clean(dbutils.widgets.get(name))
    except Exception:
        return None


def _dbutils_tags(dbutils: Any) -> dict[str, str]:
    try:
        raw_tags = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags()
    except Exception:
        return {}

    tags: dict[str, str] = {}
    for key in ("jobId", "jobRunId", "taskRunId", "orgId", "workspaceId", "jobName", "taskKey", "clusterId"):
        value = _scala_map_get(raw_tags, key)
        if value:
            tags[key] = value
    return tags


def _scala_map_get(mapping: Any, key: str) -> str | None:
    try:
        value = mapping.get(key)
        if hasattr(value, "isDefined") and value.isDefined():
            return _clean(value.get())
        return _clean(value)
    except Exception:
        return None
