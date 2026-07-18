import time


class CSVLoader:

    @staticmethod
    def load_csv_to_table(
        csv_path: str,
        table_name: str,
        conn
    ):

        start = time.perf_counter()

        conn.execute(f"""
            CREATE OR REPLACE TABLE
            {table_name}
            AS
            SELECT *
            FROM read_csv_auto(
                '{csv_path}'
            )
        """)

        rows = conn.execute(f"""
            SELECT COUNT(*)
            FROM {table_name}
        """).fetchone()[0]

        print(
            f"Created {table_name} "
            f"({rows:,} rows) "
            f"in {time.perf_counter() - start:.2f}s"
        )

        return {
            "table": table_name,
            "rows": rows
        }

    @staticmethod
    def build_stateful_tables(
        table_name: str,
        conn
    ):

        gap_tables = {

            "srcip": """
                SELECT
                    srcip,
                    time - LAG(time) OVER (
                        PARTITION BY srcip
                        ORDER BY time
                    ) AS gap
                FROM {table_name}
            """,

            "dstip": """
                SELECT
                    dstip,
                    time - LAG(time) OVER (
                        PARTITION BY dstip
                        ORDER BY time
                    ) AS gap
                FROM {table_name}
            """,

            "ippair": """
                SELECT
                    srcip,
                    dstip,
                    time - LAG(time) OVER (
                        PARTITION BY
                            srcip,
                            dstip
                        ORDER BY time
                    ) AS gap
                FROM {table_name}
            """,

            "fivetuple": """
                SELECT
                    srcip,
                    dstip,
                    srcport,
                    dstport,
                    proto,
                    time - LAG(time) OVER (
                        PARTITION BY
                            srcip,
                            dstip,
                            srcport,
                            dstport,
                            proto
                        ORDER BY time
                    ) AS gap
                FROM {table_name}
            """
        }

        for name, sql in gap_tables.items():

            start = time.perf_counter()

            conn.execute(f"""
                CREATE OR REPLACE TABLE
                {table_name}_{name}_gaps
                AS
                {sql.format(
                    table_name=table_name
                )}
            """)

            print(
                f"Created "
                f"{table_name}_{name}_gaps "
                f"in "
                f"{time.perf_counter() - start:.3f}s"
            )