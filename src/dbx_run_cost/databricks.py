from __future__ import annotations

from typing import Any


def get_active_spark_session() -> Any | None:
    try:
        from pyspark.sql import SparkSession  # type: ignore
    except Exception:
        return None

    try:
        return SparkSession.getActiveSession()
    except Exception:
        return None


def row_to_dict(row: Any) -> dict[str, Any]:
    if row is None:
        return {}
    if isinstance(row, dict):
        return row
    if hasattr(row, "asDict"):
        return row.asDict(recursive=True)
    if hasattr(row, "_asdict"):
        return dict(row._asdict())
    return dict(row)
