# dbx-run-cost-py

Print and store the cost of a Databricks job run from Python or PySpark.

`dbx-run-cost-py` is built for job clusters and serverless jobs where Databricks can attribute usage to `job_id` and `job_run_id`. It reads `system.billing.usage`, joins `system.billing.list_prices`, returns a normal Python object, and can optionally append one row to a Delta table.

It does not try to hide the hard parts:

- billing records can arrive after the job finishes
- all-purpose clusters cannot be costed per job with perfect accuracy
- cloud VM charges outside Databricks DBUs are not included
- table access requires permission to Databricks system tables

The default behavior is fast: one filtered query, no polling, no background loop.

## Install

From GitHub while the project is young:

```bash
pip install git+https://github.com/ravikiranpagidi/dbx-run-cost-py.git
```

From a clone:

```bash
git clone https://github.com/ravikiranpagidi/dbx-run-cost-py.git
cd dbx-run-cost-py
PYTHONPATH=src python -m unittest discover -s tests
```

## Quick Start In A Databricks Job

Pass Databricks dynamic values into the task as parameters or widgets:

| Parameter | Value |
| --- | --- |
| `job_id` | `{{job.id}}` |
| `job_run_id` | `{{job.run_id}}` |
| `job_name` | `{{job.name}}` |
| `task_run_id` | `{{task.run_id}}` |
| `task_name` | `{{task.name}}` |
| `run_date` | `{{job.start_time.iso_date}}` |
| `dbx_cost_tag` | `daily_orders` |
| `dbx_cost_target_table` | `prod.sales.orders` |

Then call the library near the end of the job:

```python
from dbx_run_cost import report_current_run


report = report_current_run(
    spark=spark,
    job_id=dbutils.widgets.get("job_id"),
    job_run_id=dbutils.widgets.get("job_run_id"),
    job_name=dbutils.widgets.get("job_name"),
    task_run_id=dbutils.widgets.get("task_run_id"),
    task_name=dbutils.widgets.get("task_name"),
    run_date=dbutils.widgets.get("run_date"),
    job_tag=dbutils.widgets.get("dbx_cost_tag"),
    target_table=dbutils.widgets.get("dbx_cost_target_table"),
)

print(report.summary())

cost = report.cost
dbus = report.dbus
cluster_ids = report.cluster_ids
```

## Write One Row To A Delta Table

Use `write_table` when you want this library to append the cost record.

```python
from dbx_run_cost import report_current_run


report = report_current_run(
    spark=spark,
    job_id=dbutils.widgets.get("job_id"),
    job_run_id=dbutils.widgets.get("job_run_id"),
    job_name=dbutils.widgets.get("job_name"),
    job_tag="daily_orders",
    target_table="prod.sales.orders",
    write_table="ops.job_run_costs",
)
```

The table row includes:

- job, task, workspace, and run identifiers
- `job_tag` for your own tracking label
- `target_table` for the pipeline output table or object
- DBUs, cost, currency, SKUs, cluster IDs, warehouse IDs
- usage start/end timestamps
- query latency and warning text
- JSON payload with the full report

If you prefer full control, do not pass `write_table`:

```python
report = report_current_run(spark=spark, job_id="123", job_run_id="456")

spark.createDataFrame([report.to_table_row()]).write.format("delta").mode("append").saveAsTable(
    "ops.job_run_costs"
)
```

Or write it anywhere:

```python
row = report.to_dict()
```

## Billing Data May Not Be Ready Yet

By default the library does not wait:

```python
report = report_current_run(spark=spark, job_id="123", job_run_id="456")
```

If the billing row has not landed, the report status is `not_found` and the call returns quickly.

For a final audit task, you can wait for a short time:

```python
report = report_current_run(
    spark=spark,
    job_id="123",
    job_run_id="456",
    wait_seconds=120,
    poll_seconds=30,
)
```

Keep that value small. Waiting inside a Databricks job can itself add cost.

## Pure Python Usage

The core objects have no Spark dependency:

```python
from dbx_run_cost import CostReport


report = CostReport.estimated(
    job_id="123",
    job_run_id="456",
    dbus=8.2,
    cost=1.64,
    currency_code="USD",
    job_tag="daily_orders",
)

payload = report.to_dict()
```

## CLI

Inside Databricks or any environment with an active Spark session:

```bash
dbx-run-cost report --job-id 123 --job-run-id 456 --format text
dbx-run-cost report --job-id 123 --job-run-id 456 --format json
dbx-run-cost sql --job-id 123 --job-run-id 456
```

## Accuracy

The accurate path is:

```text
system.billing.usage
JOIN system.billing.list_prices
```

Databricks documents that `usage_metadata.job_id` and `usage_metadata.job_run_id` are populated for jobs running on job compute or serverless compute. That is why this library focuses on those scenarios.

For all-purpose clusters, use the report as approximate only. Multiple users or notebooks can share the same cluster, so individual job cost is not cleanly attributable.

## Good First PRs

- add Databricks SQL warehouse connector support for running the same query outside Spark
- add a `merge` writer that upserts by `workspace_id`, `job_id`, and `job_run_id`
- add a REST helper to fetch job/run metadata when users provide a host and token
- add Slack or Teams message formatting
- add cloud VM cost estimates when users provide instance prices
- add OpenLineage event output

See [CONTRIBUTING.md](./CONTRIBUTING.md).

For release steps, see [docs/pypi-release.md](./docs/pypi-release.md).

## References

- Databricks billable usage table: `system.billing.usage`
- Databricks pricing table: `system.billing.list_prices`
- Databricks dynamic value references: `{{job.id}}`, `{{job.run_id}}`, `{{job.name}}`

## License

MIT
