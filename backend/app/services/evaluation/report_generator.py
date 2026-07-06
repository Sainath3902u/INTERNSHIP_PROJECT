import numpy as np
from collections import defaultdict


class ReportGenerator:

    @staticmethod
    def _get_category(metric_name):

        parts = metric_name.split("_")

        if metric_name.startswith("packet_"):
            return "_".join(parts[:2])

        if metric_name.startswith("flow_"):
            return "_".join(parts[:2])

        return "other"

    @staticmethod
    def _get_metric_type(metric_name):

        if metric_name.endswith("distribution"):
            return "distribution"

        if metric_name.endswith("topnkey"):
            return "topnkey"

        if metric_name.endswith("topnvalue"):
            return "topnvalue"

        return "other"

    @classmethod
    def generate(cls, results):

        metrics = []

        for result in results:
            for metric in result["metrics"]:

                metrics.append({
                    "query_id": result["query_id"],
                    "query_section": result["query_section"],
                    "query_description": result["query_description"],

                    **metric,

                    "score": round(float(metric["score"]), 4)
                })

        if not metrics:
            return {
                "overall": {},
                "percentiles": {},
                "by_category": {},
                "by_metric_type": {},
                "best_5": [],
                "worst_5": []
            }

        scores = [m["score"] for m in metrics]

        report = {}

        # Overall Statistics
        report["overall"] = {
            "avg": round(float(np.mean(scores)), 4),
            "median": round(float(np.median(scores)), 4),
            "min": round(float(np.min(scores)), 4),
            "max": round(float(np.max(scores)), 4),
            "std": round(float(np.std(scores)), 4),
            "count": len(scores)
        }

        # Percentiles
        percentiles = [5, 10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 95]

        report["percentiles"] = {
            p: round(float(np.percentile(scores, p)), 4)
            for p in percentiles
        }

        # By Category
        category_groups = defaultdict(list)

        for metric in metrics:

            category = cls._get_category(
                metric["metric"]
            )

            category_groups[category].append(
                metric["score"]
            )

        by_category = {}

        for category, values in category_groups.items():

            by_category[category] = {
                "avg": round(float(np.mean(values)), 4),
                "min": round(float(np.min(values)), 4),
                "max": round(float(np.max(values)), 4),
                "count": len(values)
            }

        report["by_category"] = by_category

        # By Metric Type
        type_groups = defaultdict(list)

        for metric in metrics:

            metric_type = cls._get_metric_type(
                metric["metric"]
            )

            type_groups[metric_type].append(
                metric["score"]
            )

        by_metric_type = {}

        for metric_type, values in type_groups.items():

            by_metric_type[metric_type] = {
                "avg": round(float(np.mean(values)), 4),
                "min": round(float(np.min(values)), 4),
                "max": round(float(np.max(values)), 4),
                "count": len(values)
            }

        report["by_metric_type"] = by_metric_type

        # Best / Worst Metrics
        report["best_5"] = sorted(
            metrics,
            key=lambda x: x["score"]
        )[:5]

        report["worst_5"] = sorted(
            metrics,
            key=lambda x: x["score"],
            reverse=True
        )[:5]

        return report