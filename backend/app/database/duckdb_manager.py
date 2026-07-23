# import duckdb


# class DuckDBManager:

#     @staticmethod
#     def connect(database_path: str, read_only: bool = False):
#         return duckdb.connect(database_path, read_only=read_only)


import duckdb

class DuckDBManager:

    @staticmethod
    def connect(database_path: str, read_only: bool = False):
        conn = duckdb.connect(database_path, read_only=read_only)
        
        # Configure memory safety limits for cloud hosting (e.g. Render 512MB RAM limit)
        conn.execute("SET max_memory = '384MB';")
        conn.execute("SET threads = 2;")
        conn.execute("SET preserve_insertion_order = false;")
        
        return conn