from __future__ import annotations

from datetime import date


def quote_sql(value: object) -> str:
    text = str(value)
    return "'" + text.replace("'", "''") + "'"


def build_job_run_cost_sql(
    *,
    job_id: str,
    job_run_id: str,
    workspace_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    lookback_days: int = 7,
) -> str:
    if not job_id:
        raise ValueError("job_id is required")
    if not job_run_id:
        raise ValueError("job_run_id is required")
    if lookback_days < 1:
        raise ValueError("lookback_days must be at least 1")

    where = [
        f"usage.usage_metadata.job_id = {quote_sql(job_id)}",
        f"usage.usage_metadata.job_run_id = {quote_sql(job_run_id)}",
        "usage.usage_metadata.job_id IS NOT NULL",
        "usage.usage_metadata.job_run_id IS NOT NULL",
    ]

    if workspace_id:
        where.append(f"usage.workspace_id = {quote_sql(workspace_id)}")

    if start_date:
        _validate_date(start_date)
        where.append(f"usage.usage_date >= DATE {quote_sql(start_date)}")
    else:
        where.append(f"usage.usage_date >= date_sub(current_date(), {int(lookback_days)})")

    if end_date:
        _validate_date(end_date)
        where.append(f"usage.usage_date <= DATE {quote_sql(end_date)}")

    where_sql = "\n      AND ".join(where)

    return f"""
WITH priced_usage AS (
  SELECT
    usage.account_id,
    usage.workspace_id,
    usage.usage_metadata.job_id AS job_id,
    usage.usage_metadata.job_run_id AS job_run_id,
    usage.usage_metadata.job_name AS job_name,
    usage.usage_metadata.cluster_id AS cluster_id,
    usage.usage_metadata.warehouse_id AS warehouse_id,
    usage.sku_name,
    usage.cloud,
    usage.usage_unit,
    list_prices.currency_code AS currency_code,
    CAST(usage.usage_quantity AS DOUBLE) AS usage_quantity,
    usage.usage_start_time,
    usage.usage_end_time,
    usage.usage_date,
    CAST(usage.usage_quantity AS DOUBLE) *
      CAST(list_prices.pricing.effective_list.default AS DOUBLE) AS list_cost
  FROM system.billing.usage AS usage
  LEFT JOIN system.billing.list_prices AS list_prices
    ON list_prices.sku_name = usage.sku_name
    AND list_prices.cloud = usage.cloud
    AND usage.usage_end_time >= list_prices.price_start_time
    AND (list_prices.price_end_time IS NULL OR usage.usage_end_time < list_prices.price_end_time)
  WHERE {where_sql}
),
line_items AS (
  SELECT
    sku_name,
    cloud,
    usage_unit,
    currency_code,
    cluster_id,
    warehouse_id,
    SUM(usage_quantity) AS dbus,
    SUM(COALESCE(list_cost, 0D)) AS cost,
    COUNT(*) AS records
  FROM priced_usage
  GROUP BY sku_name, cloud, usage_unit, currency_code, cluster_id, warehouse_id
)
SELECT
  FIRST(account_id, TRUE) AS account_id,
  FIRST(workspace_id, TRUE) AS workspace_id,
  FIRST(job_id, TRUE) AS job_id,
  FIRST(job_run_id, TRUE) AS job_run_id,
  FIRST(job_name, TRUE) AS job_name,
  MIN(usage_start_time) AS usage_start_time,
  MAX(usage_end_time) AS usage_end_time,
  SUM(usage_quantity) AS dbus,
  SUM(COALESCE(list_cost, 0D)) AS cost,
  FIRST(currency_code, TRUE) AS currency_code,
  FIRST(cloud, TRUE) AS cloud,
  COUNT(*) AS usage_records,
  COLLECT_SET(sku_name) AS sku_names,
  COLLECT_SET(cluster_id) AS cluster_ids,
  COLLECT_SET(warehouse_id) AS warehouse_ids,
  (
    SELECT TO_JSON(COLLECT_LIST(NAMED_STRUCT(
      'sku_name', sku_name,
      'cloud', cloud,
      'usage_unit', usage_unit,
      'currency_code', currency_code,
      'cluster_id', cluster_id,
      'warehouse_id', warehouse_id,
      'dbus', dbus,
      'cost', cost,
      'records', records
    )))
    FROM line_items
  ) AS line_items_json
FROM priced_usage
""".strip()


def _validate_date(value: str) -> None:
    date.fromisoformat(value)
