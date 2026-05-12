from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from dbx_run_cost.cli import main


class CliTests(unittest.TestCase):
    def test_sql_command_prints_query(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(["sql", "--job-id", "123", "--job-run-id", "456"])

        self.assertEqual(0, code)
        self.assertIn("system.billing.usage", output.getvalue())
        self.assertIn("'123'", output.getvalue())


if __name__ == "__main__":
    unittest.main()
