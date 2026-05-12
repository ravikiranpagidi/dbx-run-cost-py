from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from dbx_run_cost.context import RunContext


class ContextTests(unittest.TestCase):
    def test_context_from_env(self) -> None:
        with patch.dict(
            os.environ,
            {
                "DBX_COST_JOB_ID": "123",
                "DBX_COST_JOB_RUN_ID": "456",
                "DBX_COST_JOB_TAG": "daily_orders",
            },
            clear=True,
        ):
            context = RunContext.from_env()

        self.assertEqual("123", context.job_id)
        self.assertEqual("456", context.job_run_id)
        self.assertEqual("daily_orders", context.job_tag)

    def test_dynamic_value_placeholders_are_ignored(self) -> None:
        with patch.dict(os.environ, {"DBX_COST_JOB_ID": "{{job.id}}"}, clear=True):
            context = RunContext.from_env()

        self.assertIsNone(context.job_id)


if __name__ == "__main__":
    unittest.main()
