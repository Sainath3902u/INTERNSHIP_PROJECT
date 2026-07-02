from app.services.evaluation.metric_runner import MetricRunner

import time

class BaseRunner:

    QUERIES = []

    @classmethod
    def run_query(cls, db, query):
        start_time = time.perf_counter()

        real_sql = query["sql"].format(table_name="real_packets")
        synthetic_sql = query["sql"].format(table_name="synthetic_packets")

        real_result = db.execute_query(real_sql)
        synthetic_result = db.execute_query(synthetic_sql)

        query_time = time.perf_counter() - start_time

        results = []

        for metric_name in query["metric"]:

            score = MetricRunner.compute(
                metric_name,
                real_result,
                synthetic_result
            )

            results.append({
                "query_id": query["id"],
                # "query_section": query["section"],
                # "query_description": query["description"],
                # "sql": query["sql"],
                "metric": metric_name,
                "score": round(score, 4),
                "query_exec_time_sec": round(query_time, 4),
            })

        return results

    @classmethod
    def run_all(cls, db):

        results = []

        for query in cls.QUERIES:
            results.extend(cls.run_query(db, query))

        return results