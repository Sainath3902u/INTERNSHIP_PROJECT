import math
import pandas as pd
import numpy as np

def sample_rank_distribution(max_len: int, n_points: int = 500):
    """
    Generate logarithmically spaced indices for visualization
    while preserving detail in the distribution head.

    Parameters
    max_len : int - Length of the full ranked distribution.
    n_points : int - Maximum number of visualization points.

    Returns
    np.ndarray - Sorted unique indices.
    """

    if max_len <= n_points:
        return np.arange(max_len)

    idx = np.unique(
        np.logspace(
            0,
            np.log10(max_len),
            num=n_points
        ).astype(int) - 1
    )

    return np.clip(idx, 0, max_len - 1)

def downsample_numeric_distribution(
      vis_df: pd.DataFrame,
      x_col: str,
      real_col: str = "real",
      synthetic_col: str = "synthetic",
      n_points: int = 100,
  ):
      """
      Downsamples an ordered numeric distribution for visualization.

      Purpose:
          Preserve the overall distribution shape while reducing
          the number of plotted points.

      Suitable for:
          - Time distributions
          - Packet length distributions
          - Flow duration distributions
          - IAT distributions
          - Bytes distributions
          - Any numeric bucketed distribution

      Parameters
      vis_df : pd.DataFrame - DataFrame containing aligned visualization data.
      x_col : str - Ordered numeric axis column (bucket, len_bucket, duration_bucket, etc.)
      real_col : str - Real distribution column.
      synthetic_col : str - Synthetic distribution column.
      n_points : int - Maximum points to return.

      Returns
      pd.DataFrame - Downsampled dataframe suitable for line charts.
      """

      if len(vis_df) <= n_points:
          return vis_df.reset_index(drop=True)

      bin_size = math.ceil(len(vis_df) / n_points)

      return (
          vis_df
          .groupby(
              np.arange(len(vis_df)) // bin_size,
              as_index=False
          )
          .agg({
              x_col: "mean",
              real_col: "sum",
              synthetic_col: "sum"
          })
      )

def build_category_distribution(
        score,
        categories,
        real_values,
        synthetic_values,
        n=10,
    ):

        vis_df = pd.DataFrame({
            "category": categories,
            "real": real_values,
            "synthetic": synthetic_values,
        })

        vis_df["importance"] = vis_df["real"]

        vis_df = (
            vis_df
            .sort_values(
                "importance",
                ascending=False
            )
            .head(n)
        )

        return {
            "score": round(float(score), 4),

            "visualization": {
                "type": "grouped_bar",
                "flag": "distribution",
                "labels": [
                    str(x)
                    for x in vis_df["category"]
                ],
                "real": vis_df["real"].tolist(),
                "synthetic": vis_df["synthetic"].tolist()
            }
        }


def build_single_value(score, label, real, synthetic):

    return {
        "score": round(float(score), 4),

        "visualization": {
            "type": "dual_bar",
            "label": label,
            "real": real,
            "synthetic": synthetic
        }
    }

def build_distribution(score, labels, real, synthetic, max_len=500):
    vis_idx = sample_rank_distribution(max_len)

    return {
        "score": round(float(score), 4),

        "visualization": {
            "type": "distribution",
            "ranks": (vis_idx + 1).tolist(),
            "real": real[vis_idx].tolist(),
            "synthetic": synthetic[vis_idx].tolist()
        }
    }

def build_topnkey(score, real_keys, synthetic_keys):

    return {
        "score": round(float(score), 4),

        "visualization": {
            "type": "topnkey",
            "real": [str(x) for x in real_keys],
            "synthetic": [str(x) for x in synthetic_keys]
        }
    }

def build_topn(score, labels, real, synthetic):

    return {
        "score": round(float(score), 4),

        "visualization": {
            "type": "grouped_bar",
            "flag": "topn",
            "labels": list(labels),
            "real": [float(x) for x in real],
            "synthetic": [float(x) for x in synthetic]
        }
    }

