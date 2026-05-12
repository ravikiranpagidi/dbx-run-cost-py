from dbx_run_cost import report_current_run


report = report_current_run(
    spark=spark,
    job_id="123",
    job_run_id="456",
    job_tag="daily_orders",
    target_table="prod.sales.orders",
)

row = report.to_table_row()

spark.createDataFrame([row]).write.format("delta").mode("append").saveAsTable(
    "ops.job_run_costs"
)
