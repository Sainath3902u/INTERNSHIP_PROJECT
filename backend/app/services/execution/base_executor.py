from app.services.evaluation.metric_runner import MetricRunner
import time


class BaseRunner:

    QUERIES = []

    @classmethod
    def run_query(cls, conn, query):

        start_time = time.perf_counter()

        real_sql = query["sql"].format(table_name="real_packets")
        synthetic_sql = query["sql"].format(table_name="synthetic_packets")

        real_result = conn.execute(real_sql).fetchdf()
        synthetic_result = conn.execute(synthetic_sql).fetchdf()

        query_time = time.perf_counter() - start_time

        metrics = []

        for metric_name in query["metric"]:

            result = MetricRunner.compute(
                metric_name,
                real_result,
                synthetic_result
            )

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
            "metrics": metrics,
            "query_exec_time_sec": round(query_time, 4),
        }

    @classmethod
    def run_all(cls, conn):

        results = []

        for query in cls.QUERIES:
            results.append(
                cls.run_query(conn, query)
            )

        return results