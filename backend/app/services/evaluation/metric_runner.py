import app.services.evaluation.metric_imports as metrics

class MetricRunner:

    @staticmethod
    def compute(
        metric_name,
        real_df,
        synthetic_df
    ):

        metric_func = getattr(
            metrics,
            metric_name,
            None
        )

        if metric_func is None:
            return None
       
        return metric_func(
            real_df,
            synthetic_df
        ) 