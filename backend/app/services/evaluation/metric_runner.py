import traceback

import app.services.evaluation.metric_imports as metrics


class MetricComputationError(Exception):
    """Raised when a metric cannot be computed. Carries structured detail
    so the caller can record a per-metric failure instead of crashing
    the whole evaluation job."""

    def __init__(self, metric_name, reason):
        self.metric_name = metric_name
        self.reason = reason
        super().__init__(f"{metric_name}: {reason}")

class MetricRunner:

    @staticmethod
    def compute(
        metric_name,
        real_df,
        synthetic_df
    ):
        """
        Never raises. Always returns a dict. On failure, returns:
            {"status": "error", "score": None, "error": "<reason>"}
        so a single broken metric can never take down the rest of the job.
        """

        metric_func = getattr(
            metrics,
            metric_name,
            None
        )

        if metric_func is None:
            return {
                "status": "error",
                "score": None,
                "error": f"Unknown metric '{metric_name}' "
                         f"(not found in metric_imports)"
            }

        try:
            result = metric_func(real_df, synthetic_df)

            if result is None:
                raise MetricComputationError(
                    metric_name,
                    "metric function returned None"
                )

            result.setdefault("status", "ok")
            return result

        except Exception as e:
            traceback.print_exc()
            return {
                "status": "error",
                "score": None,
                "error": f"{type(e).__name__}: {e}"
            }