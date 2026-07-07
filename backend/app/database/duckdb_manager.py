import duckdb
class DuckDBManager:

    @staticmethod
    def connect(database_path: str):
        return duckdb.connect(database_path)