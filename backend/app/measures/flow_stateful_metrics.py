import sys
import os
import pandas as pd
import numpy as np
from scipy.spatial.distance import jensenshannon
from scipy.stats import wasserstein_distance
from tqdm import tqdm

from app.measures.packet_metrics import (
    build_topn,
    build_distribution,
    build_topnkey
)

def jensenshannon_wrapper(real_df_1, gen_df_2, base=2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between two distributions.
    """

    real_df_1 = np.asarray(real_df_1, dtype=np.float64)
    gen_df_2 = np.asarray(gen_df_2, dtype=np.float64)

    # Handle empty generated distribution
    if len(gen_df_2) == 0:
        return 1.0

    # Remove negative values
    real_df_1 = np.clip(real_df_1, 0, None)
    gen_df_2 = np.clip(gen_df_2, 0, None)

    # Keep padding for backward compatibility
    if len(gen_df_2) < len(real_df_1):
        gen_df_2 = np.pad(gen_df_2, (0, len(real_df_1) - len(gen_df_2)))
    elif len(gen_df_2) > len(real_df_1):
        real_df_1 = np.pad(real_df_1, (0, len(gen_df_2) - len(real_df_1)))

    real_sum = real_df_1.sum()
    gen_sum = gen_df_2.sum()

    # Edge cases
    if real_sum == 0 and gen_sum == 0:
        return 0.0

    if real_sum == 0 or gen_sum == 0:
        return 1.0

    # Normalize
    real_df_1 = real_df_1 / real_sum
    gen_df_2 = gen_df_2 / gen_sum

    return jensenshannon(real_df_1, gen_df_2, base=base)

def wasserstein_distance_wrapper(real_df_1, gen_df_2):
    if len(gen_df_2) == 0:
        return 1.0
    else:
        return wasserstein_distance(real_df_1, gen_df_2)

def topn_value_distance(real_values, gen_values, eps=1e-12):
    """
    Relative L1 distance between two non-negative vectors.

    d(x, y) = (1/n) * sum_i |x_i - y_i| / (x_i + y_i + eps)

    Parameters
    ----------
    real_values : array-like, shape (n,)
        Ground-truth values (non-negative).
    gen_values : array-like, shape (n,)
        Generated values (non-negative).
    eps : float
        Small constant to avoid division by zero.

    Returns
    -------
    float
        Distance in [0, 1].
    """
    real = np.asarray(real_values, dtype=np.float64)
    gen  = np.asarray(gen_values, dtype=np.float64)

    assert real.shape == gen.shape, "Input vectors must have the same shape"

    numerator = np.abs(real - gen)
    denominator = real + gen + eps

    return np.mean(numerator / denominator)


# Per Source IP
def flow_srcip_stateful_avgpacketinterval_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the average
    packet inter-arrival times for the top N source IPs.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT srcip,
                   time - LAG(time) OVER (
                       PARTITION BY srcip
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT srcip, AVG(gap) AS avg_interval
        FROM gaps
        GROUP BY srcip
        HAVING COUNT(*) > 10
        ORDER BY avg_interval DESC

        Therefore, each DataFrame contains one row per source IP with
        the average packet inter-arrival time in the 'avg_interval' column.
    """

    # Extract top-N average inter-arrival times from SQL aggregation results
    real_intervals = real_df_1["avg_interval"].to_numpy()[:n]
    gen_intervals = gen_df_2["avg_interval"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_intervals), len(gen_intervals))
    real_intervals = np.pad(real_intervals, (0, max_len - len(real_intervals)))
    gen_intervals = np.pad(gen_intervals, (0, max_len - len(gen_intervals)))

    score = topn_value_distance(real_intervals, gen_intervals)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_intervals,
        gen_intervals
    )

def flow_srcip_stateful_avgpacketinterval_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of average packet inter-arrival times per source IP.

    The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT srcip,
                   time - LAG(time) OVER (
                       PARTITION BY srcip
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT srcip, AVG(gap) AS avg_interval
        FROM gaps
        GROUP BY srcip
        HAVING COUNT(*) > 10
        ORDER BY avg_interval DESC

    Each DataFrame contains one row per source IP with
    the average packet inter-arrival time in the
    'avg_interval' column.
    """

    real_intervals = real_df_1["avg_interval"].to_numpy()
    gen_intervals = gen_df_2["avg_interval"].to_numpy()

    real_dist = (
        real_intervals / real_intervals.sum()
        if real_intervals.sum() > 0
        else np.zeros_like(real_intervals, dtype=float)
    )

    gen_dist = (
        gen_intervals / gen_intervals.sum()
        if gen_intervals.sum() > 0
        else np.zeros_like(gen_intervals, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )

def flow_srcip_stateful_flowduration_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the flow durations
    for the top N source IPs.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcip, MAX(time) - MIN(time) AS duration
        FROM <table_name>
        GROUP BY srcip
        ORDER BY duration DESC

        Therefore, each DataFrame contains one row per source IP with
        the flow duration in the 'duration' column.
    """

    # Extract top-N durations from SQL aggregation results
    real_top = real_df_1["duration"].to_numpy()[:n]
    gen_top = gen_df_2["duration"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_top), len(gen_top))
    real_top = np.pad(real_top, (0, max_len - len(real_top)))
    gen_top = np.pad(gen_top, (0, max_len - len(gen_top)))

    score = topn_value_distance(real_top, gen_top)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_top,
        gen_top
    )

def flow_srcip_stateful_flowduration_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the flow-duration
    distributions of source IPs.

    The inputs are SQL aggregation results generated from:

        SELECT srcip,
               MAX(time) - MIN(time) AS duration
        FROM <table_name>
        GROUP BY srcip
        ORDER BY duration DESC

    Each DataFrame contains one row per source IP with
    the flow duration in the 'duration' column.
    """

    real_duration = real_df_1["duration"].to_numpy()
    gen_duration = gen_df_2["duration"].to_numpy()

    real_dist = (
        real_duration / real_duration.sum()
        if real_duration.sum() > 0
        else np.zeros_like(real_duration, dtype=float)
    )

    gen_dist = (
        gen_duration / gen_duration.sum()
        if gen_duration.sum() > 0
        else np.zeros_like(gen_duration, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )

def flow_srcip_stateful_byterate_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of byte rates
    for the top N source IPs.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcip,
               SUM(pkt_len) /
               CASE
                   WHEN MAX(time) - MIN(time) = 0 THEN 1
                   ELSE MAX(time) - MIN(time)
               END AS byte_rate
        FROM <table_name>
        GROUP BY srcip
        HAVING COUNT(*) > 1
        ORDER BY byte_rate DESC

        Therefore, each DataFrame contains one row per source IP with
        the byte rate in the 'byte_rate' column.
    """

    # Extract top-N byte rates from SQL aggregation results
    real_rates = real_df_1["byte_rate"].to_numpy()[:n]
    gen_rates = gen_df_2["byte_rate"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_rates), len(gen_rates))
    real_rates = np.pad(real_rates, (0, max_len - len(real_rates)))
    gen_rates = np.pad(gen_rates, (0, max_len - len(gen_rates)))

    score = topn_value_distance(real_rates, gen_rates)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_rates,
        gen_rates
    )

def flow_srcip_stateful_byterate_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the byte-rate
    distributions of source IPs.

    The inputs are SQL aggregation results generated from:

        SELECT srcip,
               SUM(pkt_len) /
               CASE
                   WHEN MAX(time) - MIN(time) = 0 THEN 1
                   ELSE MAX(time) - MIN(time)
               END AS byte_rate
        FROM <table_name>
        GROUP BY srcip
        HAVING COUNT(*) > 1
        ORDER BY byte_rate DESC

    Each DataFrame contains one row per source IP with
    the byte rate in the 'byte_rate' column.
    """

    real_rates = real_df_1["byte_rate"].to_numpy()
    gen_rates = gen_df_2["byte_rate"].to_numpy()

    real_dist = (
        real_rates / real_rates.sum()
        if real_rates.sum() > 0
        else np.zeros_like(real_rates, dtype=float)
    )

    gen_dist = (
        gen_rates / gen_rates.sum()
        if gen_rates.sum() > 0
        else np.zeros_like(gen_rates, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )

def flow_srcip_stateful_std_interarrival_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the standard
    deviations of packet inter-arrival times for the top N source IPs.

    SQL input columns:
        srcip,
        std_iat
    """

    real_topn = real_df_1.head(n)["std_iat"].to_numpy()
    gen_topn = gen_df_2.head(n)["std_iat"].to_numpy()

    max_len = max(len(real_topn), len(gen_topn))

    real_topn = np.pad(real_topn, (0, max_len - len(real_topn)))
    gen_topn = np.pad(gen_topn, (0, max_len - len(gen_topn)))

    score = topn_value_distance(real_topn, gen_topn)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_topn,
        gen_topn
    )

def flow_srcip_stateful_std_interarrival_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of packet inter-arrival-time standard deviations for source IPs.

    SQL input columns:
        srcip,
        std_iat
    """

    real_std = real_df_1["std_iat"].to_numpy()
    gen_std = gen_df_2["std_iat"].to_numpy()

    real_dist = (
        real_std / real_std.sum()
        if real_std.sum() > 0
        else np.zeros_like(real_std, dtype=float)
    )

    gen_dist = (
        gen_std / gen_std.sum()
        if gen_std.sum() > 0
        else np.zeros_like(gen_std, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )

def flow_srcip_stateful_cv_interarrival_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the coefficients
    of variation (CV) of packet inter-arrival times for the top N source IPs.

    SQL input columns:
        srcip,
        cv_iat
    """

    real_topn = real_df_1.head(n)["cv_iat"].to_numpy()
    gen_topn = gen_df_2.head(n)["cv_iat"].to_numpy()

    max_len = max(len(real_topn), len(gen_topn))

    real_topn = np.pad(real_topn, (0, max_len - len(real_topn)))
    gen_topn = np.pad(gen_topn, (0, max_len - len(gen_topn)))

    score = topn_value_distance(real_topn, gen_topn)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_topn,
        gen_topn
    )

def flow_srcip_stateful_cv_interarrival_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between distributions
    of coefficients of variation (CV) of packet inter-arrival times.

    SQL input columns:
        srcip,
        cv_iat
    """

    real_vals = real_df_1["cv_iat"].to_numpy()
    gen_vals = gen_df_2["cv_iat"].to_numpy()

    real_dist = (
        real_vals / real_vals.sum()
        if real_vals.sum() > 0
        else np.zeros_like(real_vals, dtype=float)
    )

    gen_dist = (
        gen_vals / gen_vals.sum()
        if gen_vals.sum() > 0
        else np.zeros_like(gen_vals, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )


# Per Destination IP
def flow_dstip_stateful_avgpacketinterval_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the average
    packet inter-arrival times for the top N destination IPs.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT dstip,
                   time - LAG(time) OVER (
                       PARTITION BY dstip
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT dstip, AVG(gap) AS avg_interval
        FROM gaps
        GROUP BY dstip
        HAVING COUNT(*) > 10
        ORDER BY avg_interval DESC

        Therefore, each DataFrame contains one row per destination IP with
        the average packet inter-arrival time in the 'avg_interval' column.
    """

    # Extract top-N average inter-arrival times from SQL aggregation results
    real_intervals = real_df_1.head(n)["avg_interval"].to_numpy()
    gen_intervals = gen_df_2.head(n)["avg_interval"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_intervals), len(gen_intervals))
    real_intervals = np.pad(real_intervals, (0, max_len - len(real_intervals)))
    gen_intervals = np.pad(gen_intervals, (0, max_len - len(gen_intervals)))

    score = topn_value_distance(real_intervals, gen_intervals)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_intervals,
        gen_intervals
    )

def flow_dstip_stateful_avgpacketinterval_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of average packet inter-arrival times for destination IPs.

    SQL input columns:
        dstip,
        avg_interval
    """

    real_intervals = real_df_1["avg_interval"].to_numpy()
    gen_intervals = gen_df_2["avg_interval"].to_numpy()

    real_dist = (
        real_intervals / real_intervals.sum()
        if real_intervals.sum() > 0
        else np.zeros_like(real_intervals, dtype=float)
    )

    gen_dist = (
        gen_intervals / gen_intervals.sum()
        if gen_intervals.sum() > 0
        else np.zeros_like(gen_intervals, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )

def flow_dstip_stateful_flowduration_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the flow durations
    for the top N destination IPs.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstip, MAX(time) - MIN(time) AS duration
        FROM <table_name>
        GROUP BY dstip
        ORDER BY duration DESC

        Therefore, each DataFrame contains one row per destination IP with
        the flow duration in the 'duration' column.
    """

    # Extract top-N durations from SQL aggregation results
    real_top = real_df_1["duration"].to_numpy()[:n]
    gen_top = gen_df_2["duration"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_top), len(gen_top))
    real_top = np.pad(real_top, (0, max_len - len(real_top)))
    gen_top = np.pad(gen_top, (0, max_len - len(gen_top)))

    score = topn_value_distance(real_top, gen_top)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_top,
        gen_top
    )

def flow_dstip_stateful_flowduration_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of flow durations for destination IPs in the real and generated datasets.
    Destination IP addresses themselves are ignored; only the duration values
    and their resulting distributions are compared.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstip, MAX(time) - MIN(time) AS duration
        FROM <table_name>
        GROUP BY dstip
        ORDER BY duration DESC

        Therefore, each DataFrame contains one row per destination IP with
        the corresponding flow duration in the 'duration' column.

    Args:
        real_df_1 (pd.DataFrame): SQL aggregation result for the real dataset.
        gen_df_2 (pd.DataFrame): SQL aggregation result for the generated dataset.

    Returns:
        float: Jensen-Shannon Divergence (JSD) in [0, 1].
    """

    real_durations = real_df_1["duration"].to_numpy()
    gen_durations = gen_df_2["duration"].to_numpy()

    real_dist = (
        real_durations / real_durations.sum()
        if real_durations.sum() > 0
        else np.zeros_like(real_durations)
    )

    gen_dist = (
        gen_durations / gen_durations.sum()
        if gen_durations.sum() > 0
        else np.zeros_like(gen_durations)
    )

    # Sort distributions (dstip-agnostic comparison)
    real_sorted = np.sort(real_dist)[::-1]
    gen_sorted = np.sort(gen_dist)[::-1]

    score = jensenshannon_wrapper(real_sorted, gen_sorted, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max(len(real_sorted), len(gen_sorted)))],
        real_sorted,
        gen_sorted
    )

def flow_dstip_stateful_byterate_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of byte rates
    for the top N destination IPs.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstip,
               SUM(pkt_len) /
               CASE
                   WHEN MAX(time) - MIN(time) = 0 THEN 1
                   ELSE MAX(time) - MIN(time)
               END AS byte_rate
        FROM <table_name>
        GROUP BY dstip
        HAVING COUNT(*) > 1
        ORDER BY byte_rate DESC

        Therefore, each DataFrame contains one row per destination IP with
        the byte rate in the 'byte_rate' column.
    """

    # Extract top-N byte rates from SQL aggregation results
    real_rates = real_df_1["byte_rate"].to_numpy()[:n]
    gen_rates = gen_df_2["byte_rate"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_rates), len(gen_rates))
    real_rates = np.pad(real_rates, (0, max_len - len(real_rates)))
    gen_rates = np.pad(gen_rates, (0, max_len - len(gen_rates)))

    score = topn_value_distance(real_rates, gen_rates)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_rates,
        gen_rates
    )

def flow_dstip_stateful_byterate_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of byte rates for destination IPs in the real and generated datasets.
    Destination IP addresses themselves are ignored; only the byte-rate values
    and their resulting distributions are compared.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstip,
               SUM(pkt_len) /
               CASE
                   WHEN MAX(time) - MIN(time) = 0 THEN 1
                   ELSE MAX(time) - MIN(time)
               END AS byte_rate
        FROM <table_name>
        GROUP BY dstip
        HAVING COUNT(*) > 1
        ORDER BY byte_rate DESC

        Therefore, each DataFrame contains one row per destination IP with
        the byte rate stored in the 'byte_rate' column.

    Args:
        real_df_1 (pd.DataFrame): SQL aggregation result for the real dataset.
        gen_df_2 (pd.DataFrame): SQL aggregation result for the generated dataset.

    Returns:
        float: Jensen-Shannon Divergence (JSD) in [0, 1].
    """

    real_rates = real_df_1["byte_rate"].to_numpy()
    gen_rates = gen_df_2["byte_rate"].to_numpy()

    real_dist = (
        real_rates / real_rates.sum()
        if real_rates.sum() > 0
        else np.zeros_like(real_rates, dtype=float)
    )

    gen_dist = (
        gen_rates / gen_rates.sum()
        if gen_rates.sum() > 0
        else np.zeros_like(gen_rates, dtype=float)
    )

    real_sorted = np.sort(real_dist)[::-1]
    gen_sorted = np.sort(gen_dist)[::-1]

    score = jensenshannon_wrapper(real_sorted, gen_sorted, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max(len(real_sorted), len(gen_sorted)))],
        real_sorted,
        gen_sorted
    )

def flow_dstip_stateful_std_interarrival_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the standard
    deviations of packet inter-arrival times for the top N destination IPs.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT dstip,
                   time - LAG(time) OVER (
                       PARTITION BY dstip
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT dstip, STDDEV_POP(gap) AS std_iat
        FROM gaps
        WHERE gap IS NOT NULL
        GROUP BY dstip

        Therefore, each DataFrame contains one row per destination IP with
        the standard deviation of packet inter-arrival times in the
        'std_iat' column.
    """

    import numpy as np

    # Extract top-N std inter-arrival values from SQL aggregation results
    real_topn = real_df_1.head(n)["std_iat"].to_numpy()
    gen_topn = gen_df_2.head(n)["std_iat"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_topn), len(gen_topn))
    real_topn = np.pad(real_topn, (0, max_len - len(real_topn)))
    gen_topn = np.pad(gen_topn, (0, max_len - len(gen_topn)))

    score = topn_value_distance(real_topn, gen_topn)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_topn,
        gen_topn
    )

def flow_dstip_stateful_std_interarrival_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of standard deviations of packet inter-arrival times for destination IPs.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT dstip,
                   time - LAG(time) OVER (
                       PARTITION BY dstip
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT dstip, STDDEV_POP(gap) AS std_iat
        FROM gaps
        WHERE gap IS NOT NULL
        GROUP BY dstip
        ORDER BY std_iat DESC

        Therefore, each DataFrame contains one row per destination IP with
        the standard deviation of packet inter-arrival times in the
        'std_iat' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) in [0, 1].
    """

    real_std = real_df_1["std_iat"].to_numpy()
    gen_std = gen_df_2["std_iat"].to_numpy()

    real_dist = (
        real_std / real_std.sum()
        if real_std.sum() > 0
        else np.zeros_like(real_std, dtype=float)
    )

    gen_dist = (
        gen_std / gen_std.sum()
        if gen_std.sum() > 0
        else np.zeros_like(gen_std, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )

def flow_dstip_stateful_cv_interarrival_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the coefficients
    of variation (CV) of packet inter-arrival times for the top N destination IPs.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT dstip,
                   time - LAG(time) OVER (
                       PARTITION BY dstip
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT dstip,
               STDDEV_POP(gap) / AVG(gap) AS cv_iat
        FROM gaps
        WHERE gap IS NOT NULL
        GROUP BY dstip
        HAVING AVG(gap) > 0

        Therefore, each DataFrame contains one row per destination IP with
        the coefficient of variation of packet inter-arrival times in
        the 'cv_iat' column.
    """

    # Extract top-N CV values from SQL aggregation results
    real_topn = real_df_1.head(n)["cv_iat"].to_numpy()
    gen_topn = gen_df_2.head(n)["cv_iat"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_topn), len(gen_topn))
    real_topn = np.pad(real_topn, (0, max_len - len(real_topn)))
    gen_topn = np.pad(gen_topn, (0, max_len - len(gen_topn)))

    score = topn_value_distance(real_topn, gen_topn)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_topn,
        gen_topn
    )

def flow_dstip_stateful_cv_interarrival_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of coefficients of variation (CV) of packet inter-arrival times for
    destination IPs.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT dstip,
                   time - LAG(time) OVER (
                       PARTITION BY dstip
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT dstip,
               STDDEV_POP(gap) / AVG(gap) AS cv_iat
        FROM gaps
        WHERE gap IS NOT NULL
        GROUP BY dstip
        HAVING AVG(gap) > 0
        ORDER BY cv_iat DESC

        Therefore, each DataFrame contains one row per destination IP with
        the coefficient of variation of packet inter-arrival times in the
        'cv_iat' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) in [0, 1].
    """

    real_cv = real_df_1["cv_iat"].to_numpy()
    gen_cv = gen_df_2["cv_iat"].to_numpy()

    real_dist = (
        real_cv / real_cv.sum()
        if real_cv.sum() > 0
        else np.zeros_like(real_cv, dtype=float)
    )

    gen_dist = (
        gen_cv / gen_cv.sum()
        if gen_cv.sum() > 0
        else np.zeros_like(gen_cv, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )


# Per IP Pair
def flow_ippair_stateful_avgpacketinterval_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the average
    packet inter-arrival times for the top N source-destination IP pairs.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT srcip,
                   dstip,
                   time - LAG(time) OVER (
                       PARTITION BY srcip, dstip
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT srcip, dstip, AVG(gap) AS avg_interval
        FROM gaps
        GROUP BY srcip, dstip
        HAVING COUNT(*) > 10
        ORDER BY avg_interval DESC

        Therefore, each DataFrame contains one row per (srcip, dstip) pair
        with the average packet inter-arrival time in the 'avg_interval' column.
    """

    # Extract top-N average inter-arrival times from SQL aggregation results
    real_intervals = real_df_1.head(n)["avg_interval"].to_numpy()
    gen_intervals = gen_df_2.head(n)["avg_interval"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_intervals), len(gen_intervals))
    real_intervals = np.pad(real_intervals, (0, max_len - len(real_intervals)))
    gen_intervals = np.pad(gen_intervals, (0, max_len - len(gen_intervals)))

    score = topn_value_distance(real_intervals, gen_intervals)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_intervals,
        gen_intervals
    )

def flow_ippair_stateful_avgpacketinterval_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of average packet inter-arrival times for source-destination IP pairs.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT srcip,
                   dstip,
                   time - LAG(time) OVER (
                       PARTITION BY srcip, dstip
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT srcip, dstip, AVG(gap) AS avg_interval
        FROM gaps
        GROUP BY srcip, dstip
        HAVING COUNT(*) > 10
        ORDER BY avg_interval DESC

        Therefore, each DataFrame contains one row per (srcip, dstip) pair
        with the average packet inter-arrival time in the 'avg_interval' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) in [0, 1].
    """

    real_vals = real_df_1["avg_interval"].to_numpy()
    gen_vals = gen_df_2["avg_interval"].to_numpy()

    real_dist = (
        real_vals / real_vals.sum()
        if real_vals.sum() > 0
        else np.zeros_like(real_vals, dtype=float)
    )

    gen_dist = (
        gen_vals / gen_vals.sum()
        if gen_vals.sum() > 0
        else np.zeros_like(gen_vals, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )

def flow_ippair_stateful_flowduration_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the flow durations
    for the top N source-destination IP pairs.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcip, dstip, MAX(time) - MIN(time) AS duration
        FROM <table_name>
        GROUP BY srcip, dstip
        ORDER BY duration DESC

        Therefore, each DataFrame contains one row per (srcip, dstip) pair
        with the flow duration in the 'duration' column.
    """

    # Extract top-N durations from SQL aggregation results
    real_top = real_df_1.head(n)["duration"].to_numpy()
    gen_top = gen_df_2.head(n)["duration"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_top), len(gen_top))
    real_top = np.pad(real_top, (0, max_len - len(real_top)))
    gen_top = np.pad(gen_top, (0, max_len - len(gen_top)))

    score = topn_value_distance(real_top, gen_top)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_top,
        gen_top
    )

def flow_ippair_stateful_flowduration_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of flow durations for source-destination IP pairs.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcip,
               dstip,
               MAX(time) - MIN(time) AS duration
        FROM <table_name>
        GROUP BY srcip, dstip
        ORDER BY duration DESC

        Therefore, each DataFrame contains one row per (srcip, dstip) pair
        with the flow duration in the 'duration' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) in [0, 1].
    """

    real_vals = real_df_1["duration"].to_numpy()
    gen_vals = gen_df_2["duration"].to_numpy()

    real_dist = (
        real_vals / real_vals.sum()
        if real_vals.sum() > 0
        else np.zeros_like(real_vals, dtype=float)
    )

    gen_dist = (
        gen_vals / gen_vals.sum()
        if gen_vals.sum() > 0
        else np.zeros_like(gen_vals, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )

def flow_ippair_stateful_byterate_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of byte rates
    for the top N source-destination IP pairs.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcip,
               dstip,
               SUM(pkt_len) /
               CASE
                   WHEN MAX(time) - MIN(time) = 0 THEN 1
                   ELSE MAX(time) - MIN(time)
               END AS byte_rate
        FROM <table_name>
        GROUP BY srcip, dstip
        HAVING COUNT(*) > 1
        ORDER BY byte_rate DESC

        Therefore, each DataFrame contains one row per (srcip, dstip) pair
        with the byte rate in the 'byte_rate' column.
    """

    # Extract top-N byte rates from SQL aggregation results
    real_rates = real_df_1.head(n)["byte_rate"].to_numpy()
    gen_rates = gen_df_2.head(n)["byte_rate"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_rates), len(gen_rates))
    real_rates = np.pad(real_rates, (0, max_len - len(real_rates)))
    gen_rates = np.pad(gen_rates, (0, max_len - len(gen_rates)))

    score = topn_value_distance(real_rates, gen_rates)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_rates,
        gen_rates
    )

def flow_ippair_stateful_byterate_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of byte rates for source-destination IP pairs.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcip,
               dstip,
               SUM(pkt_len) /
               CASE
                   WHEN MAX(time) - MIN(time) = 0 THEN 1
                   ELSE MAX(time) - MIN(time)
               END AS byte_rate
        FROM <table_name>
        GROUP BY srcip, dstip
        HAVING COUNT(*) > 1
        ORDER BY byte_rate DESC

        Therefore, each DataFrame contains one row per (srcip, dstip) pair
        with the byte rate in the 'byte_rate' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) in [0, 1].
    """

    real_vals = real_df_1["byte_rate"].to_numpy()
    gen_vals = gen_df_2["byte_rate"].to_numpy()

    real_dist = (
        real_vals / real_vals.sum()
        if real_vals.sum() > 0
        else np.zeros_like(real_vals, dtype=float)
    )

    gen_dist = (
        gen_vals / gen_vals.sum()
        if gen_vals.sum() > 0
        else np.zeros_like(gen_vals, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )

def flow_ippair_stateful_std_interarrival_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the standard
    deviations of packet inter-arrival times for the top N
    source-destination IP pairs.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT srcip,
                   dstip,
                   time - LAG(time) OVER (
                       PARTITION BY srcip, dstip
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT srcip, dstip, STDDEV_POP(gap) AS std_iat
        FROM gaps
        WHERE gap IS NOT NULL
        GROUP BY srcip, dstip
        ORDER BY std_iat DESC

        Therefore, each DataFrame contains one row per (srcip, dstip) pair
        with the standard deviation of packet inter-arrival times in the
        'std_iat' column.
    """

    # Extract top-N std inter-arrival values from SQL aggregation results
    real_topn = real_df_1.head(n)["std_iat"].to_numpy()
    gen_topn = gen_df_2.head(n)["std_iat"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_topn), len(gen_topn))
    real_topn = np.pad(real_topn, (0, max_len - len(real_topn)))
    gen_topn = np.pad(gen_topn, (0, max_len - len(gen_topn)))

    score = topn_value_distance(real_topn, gen_topn)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_topn,
        gen_topn
    )

def flow_ippair_stateful_std_interarrival_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of standard deviations of packet inter-arrival times for
    source-destination IP pairs.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT srcip,
                   dstip,
                   time - LAG(time) OVER (
                       PARTITION BY srcip, dstip
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT srcip, dstip, STDDEV_POP(gap) AS std_iat
        FROM gaps
        WHERE gap IS NOT NULL
        GROUP BY srcip, dstip
        ORDER BY std_iat DESC

        Therefore, each DataFrame contains one row per (srcip, dstip) pair
        with the standard deviation of packet inter-arrival times in the
        'std_iat' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) in [0, 1].
    """

    real_std = real_df_1["std_iat"].to_numpy()
    gen_std = gen_df_2["std_iat"].to_numpy()

    real_dist = (
        real_std / real_std.sum()
        if real_std.sum() > 0
        else np.zeros_like(real_std, dtype=float)
    )

    gen_dist = (
        gen_std / gen_std.sum()
        if gen_std.sum() > 0
        else np.zeros_like(gen_std, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )

def flow_ippair_stateful_cv_interarrival_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the coefficients
    of variation (CV) of packet inter-arrival times for the top N
    source-destination IP pairs.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT srcip,
                   dstip,
                   time - LAG(time) OVER (
                       PARTITION BY srcip, dstip
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT srcip, dstip, STDDEV_POP(gap) / AVG(gap) AS cv_iat
        FROM gaps
        WHERE gap IS NOT NULL
        GROUP BY srcip, dstip
        HAVING AVG(gap) > 0

        Therefore, each DataFrame contains one row per (srcip, dstip) pair
        with the coefficient of variation of packet inter-arrival times in
        the 'cv_iat' column.
    """

    # Sort descending and take top-N, matching original behavior
    real_topn = real_df_1.head(n)["cv_iat"].to_numpy()
    gen_topn = gen_df_2.head(n)["cv_iat"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_topn), len(gen_topn))
    real_topn = np.pad(real_topn, (0, max_len - len(real_topn)))
    gen_topn = np.pad(gen_topn, (0, max_len - len(gen_topn)))

    score = topn_value_distance(real_topn, gen_topn)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_topn,
        gen_topn
    )

def flow_ippair_stateful_cv_interarrival_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of coefficients of variation (CV) of packet inter-arrival times for
    source-destination IP pairs.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT srcip,
                   dstip,
                   time - LAG(time) OVER (
                       PARTITION BY srcip, dstip
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT srcip,
               dstip,
               STDDEV_POP(gap) / AVG(gap) AS cv_iat
        FROM gaps
        WHERE gap IS NOT NULL
        GROUP BY srcip, dstip
        HAVING AVG(gap) > 0
        ORDER BY cv_iat DESC

        Therefore, each DataFrame contains one row per (srcip, dstip) pair
        with the coefficient of variation of packet inter-arrival times in
        the 'cv_iat' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) in [0, 1].
    """

    real_cv = real_df_1["cv_iat"].to_numpy()
    gen_cv = gen_df_2["cv_iat"].to_numpy()

    real_dist = (
        real_cv / real_cv.sum()
        if real_cv.sum() > 0
        else np.zeros_like(real_cv, dtype=float)
    )

    gen_dist = (
        gen_cv / gen_cv.sum()
        if gen_cv.sum() > 0
        else np.zeros_like(gen_cv, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )


# Per 5-Tuple Flow
def flow_fivetuple_stateful_avgpacketinterval_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the average
    packet inter-arrival times for the top N 5-tuple flows.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT srcip, dstip, srcport, dstport, proto,
                   time - LAG(time) OVER (
                       PARTITION BY srcip, dstip, srcport, dstport, proto
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT srcip, dstip, srcport, dstport, proto,
               AVG(gap) AS avg_interval
        FROM gaps
        GROUP BY srcip, dstip, srcport, dstport, proto
        HAVING COUNT(*) > 10
        ORDER BY avg_interval DESC

        Therefore, each DataFrame contains one row per 5-tuple flow with
        the average packet inter-arrival time in the 'avg_interval' column.
    """

    # Extract top-N average inter-arrival times from SQL aggregation results
    real_intervals = real_df_1.head(n)["avg_interval"].to_numpy()
    gen_intervals = gen_df_2.head(n)["avg_interval"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_intervals), len(gen_intervals))
    real_intervals = np.pad(real_intervals, (0, max_len - len(real_intervals)))
    gen_intervals = np.pad(gen_intervals, (0, max_len - len(gen_intervals)))

    score = topn_value_distance(real_intervals, gen_intervals)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_intervals,
        gen_intervals
    )

def flow_fivetuple_stateful_avgpacketinterval_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of average packet inter-arrival times for 5-tuple flows.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT srcip, dstip, srcport, dstport, proto,
                   time - LAG(time) OVER (
                       PARTITION BY srcip, dstip, srcport, dstport, proto
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT srcip, dstip, srcport, dstport, proto,
               AVG(gap) AS avg_interval
        FROM gaps
        GROUP BY srcip, dstip, srcport, dstport, proto
        HAVING COUNT(*) > 10
        ORDER BY avg_interval DESC

        Therefore, each DataFrame contains one row per 5-tuple flow with
        the average packet inter-arrival time in the 'avg_interval' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) in [0, 1].
    """

    real_vals = real_df_1["avg_interval"].to_numpy()
    gen_vals = gen_df_2["avg_interval"].to_numpy()

    real_dist = (
        real_vals / real_vals.sum()
        if real_vals.sum() > 0
        else np.zeros_like(real_vals, dtype=float)
    )

    gen_dist = (
        gen_vals / gen_vals.sum()
        if gen_vals.sum() > 0
        else np.zeros_like(gen_vals, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )

def flow_fivetuple_stateful_flowduration_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the flow durations
    for the top N 5-tuple flows.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcip, dstip, srcport, dstport, proto,
               MAX(time) - MIN(time) AS duration
        FROM <table_name>
        GROUP BY srcip, dstip, srcport, dstport, proto
        ORDER BY duration DESC

        Therefore, each DataFrame contains one row per 5-tuple flow with
        the flow duration in the 'duration' column.
    """

    # Extract top-N durations from SQL aggregation results
    real_top = real_df_1.head(n)["duration"].to_numpy()
    gen_top = gen_df_2.head(n)["duration"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_top), len(gen_top))
    real_top = np.pad(real_top, (0, max_len - len(real_top)))
    gen_top = np.pad(gen_top, (0, max_len - len(gen_top)))

    score = topn_value_distance(real_top, gen_top)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_top,
        gen_top
    )

def flow_fivetuple_stateful_flowduration_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of flow durations for 5-tuple flows.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcip, dstip, srcport, dstport, proto,
               MAX(time) - MIN(time) AS duration
        FROM <table_name>
        GROUP BY srcip, dstip, srcport, dstport, proto
        ORDER BY duration DESC

        Therefore, each DataFrame contains one row per 5-tuple flow with
        the flow duration in the 'duration' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) in [0, 1].
    """

    real_vals = real_df_1["duration"].to_numpy()
    gen_vals = gen_df_2["duration"].to_numpy()

    real_dist = (
        real_vals / real_vals.sum()
        if real_vals.sum() > 0
        else np.zeros_like(real_vals, dtype=float)
    )

    gen_dist = (
        gen_vals / gen_vals.sum()
        if gen_vals.sum() > 0
        else np.zeros_like(gen_vals, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )

def flow_fivetuple_stateful_byterate_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of byte rates
    for the top N 5-tuple flows.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcip, dstip, srcport, dstport, proto,
               SUM(pkt_len) /
               CASE
                   WHEN MAX(time) - MIN(time) = 0 THEN 1
                   ELSE MAX(time) - MIN(time)
               END AS byte_rate
        FROM <table_name>
        GROUP BY srcip, dstip, srcport, dstport, proto
        HAVING COUNT(*) > 1
        ORDER BY byte_rate DESC

        Therefore, each DataFrame contains one row per 5-tuple flow with
        the byte rate in the 'byte_rate' column.
    """

    # Extract top-N byte rates from SQL aggregation results
    real_rates = real_df_1.head(n)["byte_rate"].to_numpy()
    gen_rates = gen_df_2.head(n)["byte_rate"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_rates), len(gen_rates))
    real_rates = np.pad(real_rates, (0, max_len - len(real_rates)))
    gen_rates = np.pad(gen_rates, (0, max_len - len(gen_rates)))

    score = topn_value_distance(real_rates, gen_rates)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_rates,
        gen_rates
    )

def flow_fivetuple_stateful_byterate_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of byte rates for 5-tuple flows.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcip, dstip, srcport, dstport, proto,
               SUM(pkt_len) /
               CASE
                   WHEN MAX(time) - MIN(time) = 0 THEN 1
                   ELSE MAX(time) - MIN(time)
               END AS byte_rate
        FROM <table_name>
        GROUP BY srcip, dstip, srcport, dstport, proto
        HAVING COUNT(*) > 1
        ORDER BY byte_rate DESC

        Therefore, each DataFrame contains one row per 5-tuple flow with
        the byte rate in the 'byte_rate' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) in [0, 1].
    """

    real_vals = real_df_1["byte_rate"].to_numpy()
    gen_vals = gen_df_2["byte_rate"].to_numpy()

    real_dist = (
        real_vals / real_vals.sum()
        if real_vals.sum() > 0
        else np.zeros_like(real_vals, dtype=float)
    )

    gen_dist = (
        gen_vals / gen_vals.sum()
        if gen_vals.sum() > 0
        else np.zeros_like(gen_vals, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )

def flow_fivetuple_stateful_std_interarrival_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the standard
    deviations of packet inter-arrival times for the top N 5-tuple flows.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT srcip, dstip, srcport, dstport, proto,
                   time - LAG(time) OVER (
                       PARTITION BY srcip, dstip, srcport, dstport, proto
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT srcip, dstip, srcport, dstport, proto,
               STDDEV_POP(gap) AS std_iat
        FROM gaps
        WHERE gap IS NOT NULL
        GROUP BY srcip, dstip, srcport, dstport, proto
        ORDER BY std_iat DESC

        Therefore, each DataFrame contains one row per 5-tuple flow with
        the standard deviation of packet inter-arrival times in the
        'std_iat' column.
    """

    # Extract top-N std inter-arrival values from SQL aggregation results
    real_topn = real_df_1.head(n)["std_iat"].to_numpy()
    gen_topn = gen_df_2.head(n)["std_iat"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_topn), len(gen_topn))
    real_topn = np.pad(real_topn, (0, max_len - len(real_topn)))
    gen_topn = np.pad(gen_topn, (0, max_len - len(gen_topn)))

    score = topn_value_distance(real_topn, gen_topn)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_topn,
        gen_topn
    )

def flow_fivetuple_stateful_std_interarrival_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of standard deviations of packet inter-arrival times for 5-tuple flows.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT srcip, dstip, srcport, dstport, proto,
                   time - LAG(time) OVER (
                       PARTITION BY srcip, dstip, srcport, dstport, proto
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT srcip, dstip, srcport, dstport, proto,
               STDDEV_POP(gap) AS std_iat
        FROM gaps
        WHERE gap IS NOT NULL
        GROUP BY srcip, dstip, srcport, dstport, proto
        ORDER BY std_iat DESC

        Therefore, each DataFrame contains one row per 5-tuple flow with
        the standard deviation of packet inter-arrival times in the
        'std_iat' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) in [0, 1].
    """

    real_std = real_df_1["std_iat"].to_numpy()
    gen_std = gen_df_2["std_iat"].to_numpy()

    real_dist = (
        real_std / real_std.sum()
        if real_std.sum() > 0
        else np.zeros_like(real_std, dtype=float)
    )

    gen_dist = (
        gen_std / gen_std.sum()
        if gen_std.sum() > 0
        else np.zeros_like(gen_std, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )

def flow_fivetuple_stateful_cv_interarrival_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the coefficients
    of variation (CV) of packet inter-arrival times for the top N 5-tuple flows.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT srcip, dstip, srcport, dstport, proto,
                   time - LAG(time) OVER (
                       PARTITION BY srcip, dstip, srcport, dstport, proto
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT srcip, dstip, srcport, dstport, proto,
               STDDEV_POP(gap) / AVG(gap) AS cv_iat
        FROM gaps
        WHERE gap IS NOT NULL
        GROUP BY srcip, dstip, srcport, dstport, proto
        HAVING AVG(gap) > 0
        ORDER BY cv_iat DESC

        Therefore, each DataFrame contains one row per 5-tuple flow with
        the coefficient of variation of packet inter-arrival times in the
        'cv_iat' column.
    """

    # Extract top-N CV values from SQL aggregation results
    real_topn = real_df_1.head(n)["cv_iat"].to_numpy()
    gen_topn = gen_df_2.head(n)["cv_iat"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_topn), len(gen_topn))
    real_topn = np.pad(real_topn, (0, max_len - len(real_topn)))
    gen_topn = np.pad(gen_topn, (0, max_len - len(gen_topn)))

    score = topn_value_distance(real_topn, gen_topn)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_topn,
        gen_topn
    )

def flow_fivetuple_stateful_cv_interarrival_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of coefficients of variation (CV) of packet inter-arrival times for
    5-tuple flows.

    Note:
        The inputs are SQL aggregation results generated from:

        WITH gaps AS (
            SELECT srcip, dstip, srcport, dstport, proto,
                   time - LAG(time) OVER (
                       PARTITION BY srcip, dstip, srcport, dstport, proto
                       ORDER BY time
                   ) AS gap
            FROM <table_name>
        )
        SELECT srcip, dstip, srcport, dstport, proto,
               STDDEV_POP(gap) / AVG(gap) AS cv_iat
        FROM gaps
        WHERE gap IS NOT NULL
        GROUP BY srcip, dstip, srcport, dstport, proto
        HAVING AVG(gap) > 0
        ORDER BY cv_iat DESC

        Therefore, each DataFrame contains one row per 5-tuple flow with
        the coefficient of variation of packet inter-arrival times in the
        'cv_iat' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) in [0, 1].
    """

    real_cv = real_df_1["cv_iat"].to_numpy()
    gen_cv = gen_df_2["cv_iat"].to_numpy()

    real_dist = (
        real_cv / real_cv.sum()
        if real_cv.sum() > 0
        else np.zeros_like(real_cv, dtype=float)
    )

    gen_dist = (
        gen_cv / gen_cv.sum()
        if gen_cv.sum() > 0
        else np.zeros_like(gen_cv, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_dist,
        gen_dist
    )
