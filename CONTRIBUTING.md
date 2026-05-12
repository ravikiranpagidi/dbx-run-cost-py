# Contributing

Thanks for helping improve `dbx-run-cost-py`.

This project should stay small, predictable, and cheap to run. A cost reporter that quietly runs expensive queries is not useful.

## Local Setup

```bash
git clone https://github.com/ravikiranpagidi/dbx-run-cost-py.git
cd dbx-run-cost-py
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python -m dbx_run_cost sql --job-id 123 --job-run-id 456
```

No runtime dependencies are required for the core package.

## Principles

- Default to one query.
- Do not poll unless the user explicitly asks.
- Keep Spark imports optional.
- Return plain Python objects.
- Keep writes opt-in.
- Prefer clear warnings over fake precision.

## Pull Requests

Useful PRs are usually small:

- one new writer
- one new output format
- one Databricks metadata helper
- one test fixture
- one documentation improvement

Please include how you tested the change.
