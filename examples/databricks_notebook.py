from dbx_run_cost import report_current_run


report = report_current_run(
    spark=spark,  # provided by Databricks
    job_id=dbutils.widgets.get("job_id"),
    job_run_id=dbutils.widgets.get("job_run_id"),
    job_name=dbutils.widgets.get("job_name"),
    task_run_id=dbutils.widgets.get("task_run_id"),
    task_name=dbutils.widgets.get("task_name"),
    run_date=dbutils.widgets.get("run_date"),
    job_tag=dbutils.widgets.get("dbx_cost_tag"),
    target_table=dbutils.widgets.get("dbx_cost_target_table"),
    write_table="ops.job_run_costs",
)

print(report.summary())

cost = report.cost
dbus = report.dbus
