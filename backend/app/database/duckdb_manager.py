import duckdb

class DuckDBManager:
    def __init__(self):
        self.conn = None

    def connect(self):
        if self.conn is None:
            self.conn = duckdb.connect("benchmark.db")

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def execute_query(self, query):
        return self.conn.execute(query).fetchdf()