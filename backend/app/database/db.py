from app.database.duckdb_manager import DuckDBManager

def get_connection(database_path: str):
    return DuckDBManager.connect(database_path)