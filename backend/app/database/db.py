from app.database.duckdb_manager import DuckDBManager


def get_connection(database_path: str):
    """Read-write connection used for data ingestion and building tables.
    Only one should be open for a job's database at any given time."""
    return DuckDBManager.connect(database_path, read_only=False)


def get_read_connection(database_path: str):
    """Read-only connection.
    Multiple read-only connections can be open for the same database file,
    as long as no read-write connection is open. Safe to use across threads
    during the evaluation phase."""
    return DuckDBManager.connect(database_path, read_only=True)
