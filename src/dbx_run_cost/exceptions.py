class DbxRunCostError(Exception):
    """Base error for dbx-run-cost-py."""


class MissingSparkSession(DbxRunCostError):
    """Raised when a Spark session is required but not available."""
