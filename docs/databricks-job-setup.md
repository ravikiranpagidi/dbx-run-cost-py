# Databricks Job Setup

The safest way to pass run metadata into a task is with dynamic value references.

Add these parameters to the job or notebook task:

| Parameter | Value |
| --- | --- |
| `job_id` | `{{job.id}}` |
| `job_run_id` | `{{job.run_id}}` |
| `job_name` | `{{job.name}}` |
| `task_run_id` | `{{task.run_id}}` |
| `task_name` | `{{task.name}}` |
| `run_date` | `{{job.start_time.iso_date}}` |
| `dbx_cost_tag` | any label you want |
| `dbx_cost_target_table` | the table or object the job updates |

Use a final task when possible. If a multi-task job writes cost from the first task, downstream tasks might not be included in the final job-run billing total yet.

Default behavior does not wait for billing data. If your billing rows usually arrive later, schedule a small follow-up job or use `wait_seconds` with care.
