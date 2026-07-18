import time
import traceback
from concurrent.futures import ThreadPoolExecutor

from app.services.evaluation.metric_runner import MetricRunner

class BaseRunner:

    QUERIES = []

    @classmethod
    def run_query(cls, conn, query):
        """
        Runs one query (real + synthetic) and computes its metrics.
        Never raises: SQL errors and metric errors are both caught and
        turned into an "error" entry so one bad query can't take down
        the rest of the job.
        """

        start_time = time.perf_counter()

        try:
            real_sql = query["sql"].format(table_name="real_packets")
            synthetic_sql = query["sql"].format(table_name="synthetic_packets")

            real_result = conn.execute(real_sql).fetchdf()
            synthetic_result = conn.execute(synthetic_sql).fetchdf()

        except Exception as e:
            traceback.print_exc()

            return {
                "query_id": query["id"],
                "query_section": query["section"],
                "query_description": query["description"],
                "sql": query["sql"],
                "status": "error",
                "error": f"Query execution failed: {type(e).__name__}: {e}",
                "metrics": [],
                "query_exec_time_sec": round(
                    time.perf_counter() - start_time, 4
                ),
            }

        query_time = time.perf_counter() - start_time

        metrics = []

        for metric_name in query["metric"]:

            # MetricRunner.compute never raises - always returns a dict,
            # with status "ok" or "error".
            result = MetricRunner.compute(
                metric_name,
                real_result,
                synthetic_result
            )

            if result.get("status") == "ok" and result.get("score") is not None:
                result["score"] = round(result["score"], 4)

            metrics.append({
                "metric": metric_name,
                **result
            })

        return {
            "query_id": query["id"],
            "query_section": query["section"],
            "query_description": query["description"],
            "sql": query["sql"],
            "status": "ok",
            "metrics": metrics,
            "query_exec_time_sec": round(query_time, 4),
        }

    @classmethod
    def run_all(cls, conn, max_workers: int = 1):
        """
        Run all queries in cls.QUERIES.

        With max_workers=1, queries run sequentially.

        With max_workers>1, queries run in parallel using separate cursors
        on the same connection. DuckDB supports concurrent cursor usage and
        releases the GIL during query execution, so parallel execution
        provides a real performance benefit.
        """

        if max_workers <= 1 or len(cls.QUERIES) <= 1:
            return [
                cls.run_query(conn, query)
                for query in cls.QUERIES
            ]

        results = [None] * len(cls.QUERIES)

        def _run(index, query):
            # Each task gets its own cursor so concurrent queries don't
            # stomp on each other's result state on the same connection.
            cursor = conn.cursor()
            try:
                return index, cls.run_query(cursor, query)
            finally:
                cursor.close()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(_run, i, query)
                for i, query in enumerate(cls.QUERIES)
            ]

            for future in futures:
                index, result = future.result()
                results[index] = result

        return results