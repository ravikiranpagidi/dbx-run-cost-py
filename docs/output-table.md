# Output Table

`write_delta_report` writes one row per report.

Recommended table name:

```text
ops.job_run_costs
```

Useful columns:

- `report_created_at`
- `status`
- `source`
- `workspace_id`
- `job_id`
- `job_run_id`
- `task_run_id`
- `job_name`
- `task_name`
- `job_tag`
- `target_table`
- `dbus`
- `cost`
- `currency_code`
- `cluster_ids_json`
- `sku_names_json`
- `usage_start_time`
- `usage_end_time`
- `warnings_json`
- `payload_json`

The JSON columns keep the table schema stable while preserving detail.
