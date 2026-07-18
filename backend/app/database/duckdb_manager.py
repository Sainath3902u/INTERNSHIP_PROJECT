import duckdb


class DuckDBManager:

    @staticmethod
    def connect(database_path: str, read_only: bool = False):
        return duckdb.connect(database_path, read_only=read_only)
