import pandas as pd
import numpy as np
from scipy.spatial.distance import jensenshannon
from scipy.stats import wasserstein_distance
from tqdm import tqdm

from app.measures.response_builders import *

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
    """

    # Extract top-N average inter-arrival times from SQL aggregation results
    real_intervals = real_df_1["avg_interval"].to_numpy()[:n]
    gen_intervals = gen_df_2["avg_interval"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_intervals), len(gen_intervals))
    real_intervals = np.pad(real_intervals, (0, max_len - len(real_intervals)))
    gen_intervals = np.pad(gen_intervals, (0, max_len - len(gen_intervals)))

    score = topn_value_distance(real_intervals, gen_intervals)

    real_vis = real_intervals / 1e9
    gen_vis = gen_intervals / 1e9

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_vis,
        gen_vis,
        "s"
    )

def flow_srcip_stateful_avgpacketinterval_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of average packet inter-arrival times per source IP.
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
    """

    # Extract top-N durations from SQL aggregation results
    real_top = real_df_1["duration"].to_numpy()[:n]
    gen_top = gen_df_2["duration"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_top), len(gen_top))
    real_top = np.pad(real_top, (0, max_len - len(real_top)))
    gen_top = np.pad(gen_top, (0, max_len - len(gen_top)))

    score = topn_value_distance(real_top, gen_top)

    real_vis = real_top / 1e9
    gen_vis = gen_top / 1e9

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_vis,
        gen_vis,
        "s"
    )

def flow_srcip_stateful_flowduration_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the flow-duration
    distributions of source IPs.
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
    """

    # Extract top-N byte rates from SQL aggregation results
    real_rates = real_df_1["byte_rate"].to_numpy()[:n]
    gen_rates = gen_df_2["byte_rate"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_rates), len(gen_rates))
    real_rates = np.pad(real_rates, (0, max_len - len(real_rates)))
    gen_rates = np.pad(gen_rates, (0, max_len - len(gen_rates)))

    score = topn_value_distance(real_rates, gen_rates)

    real_vis = real_rates * 1e6 / (1024 * 1024)
    gen_vis  = gen_rates  * 1e6 / (1024 * 1024)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_vis,
        gen_vis,
        "MB/s"
    )

def flow_srcip_stateful_byterate_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the byte-rate
    distributions of source IPs.
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
    """

    real_topn = real_df_1.head(n)["std_iat"].to_numpy()
    gen_topn = gen_df_2.head(n)["std_iat"].to_numpy()

    max_len = max(len(real_topn), len(gen_topn))

    real_topn = np.pad(real_topn, (0, max_len - len(real_topn)))
    gen_topn = np.pad(gen_topn, (0, max_len - len(gen_topn)))

    score = topn_value_distance(real_topn, gen_topn)

    real_vis = real_topn / 1e9
    gen_vis = gen_topn / 1e9

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_vis,
        gen_vis,
        "s"
    )

def flow_srcip_stateful_std_interarrival_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of packet inter-arrival-time standard deviations for source IPs.
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
        gen_topn,
        "CV"
    )

def flow_srcip_stateful_cv_interarrival_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between distributions
    of coefficients of variation (CV) of packet inter-arrival times.
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
    """

    # Extract top-N average inter-arrival times from SQL aggregation results
    real_intervals = real_df_1.head(n)["avg_interval"].to_numpy()
    gen_intervals = gen_df_2.head(n)["avg_interval"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_intervals), len(gen_intervals))
    real_intervals = np.pad(real_intervals, (0, max_len - len(real_intervals)))
    gen_intervals = np.pad(gen_intervals, (0, max_len - len(gen_intervals)))

    score = topn_value_distance(real_intervals, gen_intervals)

    real_vis = real_intervals / 1e6
    gen_vis = gen_intervals / 1e6
    
    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_vis,
        gen_vis,
        "s"
    )

def flow_dstip_stateful_avgpacketinterval_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of average packet inter-arrival times for destination IPs.
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
    """

    # Extract top-N durations from SQL aggregation results
    real_top = real_df_1["duration"].to_numpy()[:n]
    gen_top = gen_df_2["duration"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_top), len(gen_top))
    real_top = np.pad(real_top, (0, max_len - len(real_top)))
    gen_top = np.pad(gen_top, (0, max_len - len(gen_top)))

    score = topn_value_distance(real_top, gen_top)

    real_vis = real_top / 1e6
    gen_vis = gen_top / 1e6

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_vis,
        gen_vis,
        "s"
    )

def flow_dstip_stateful_flowduration_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of flow durations for destination IPs in the real and generated datasets.
    Destination IP addresses themselves are ignored; only the duration values
    and their resulting distributions are compared.
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

    real_sorted = np.sort(real_dist)[::-1]
    gen_sorted = np.sort(gen_dist)[::-1]

    # Sort distributions (dstip-agnostic comparison)
    max_len = max(len(real_sorted), len(gen_sorted))

    real_sorted = np.pad(real_sorted, (0, max_len - len(real_sorted)))
    gen_sorted = np.pad(gen_sorted, (0, max_len - len(gen_sorted)))

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
    """

    # Extract top-N byte rates from SQL aggregation results
    real_rates = real_df_1["byte_rate"].to_numpy()[:n]
    gen_rates = gen_df_2["byte_rate"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_rates), len(gen_rates))
    real_rates = np.pad(real_rates, (0, max_len - len(real_rates)))
    gen_rates = np.pad(gen_rates, (0, max_len - len(gen_rates)))

    score = topn_value_distance(real_rates, gen_rates)

    real_vis = real_rates * 1e6 / (1024 * 1024)
    gen_vis  = gen_rates  * 1e6 / (1024 * 1024)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_vis,
        gen_vis,
        "MB/s"
    )

def flow_dstip_stateful_byterate_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of byte rates for destination IPs in the real and generated datasets.
    Destination IP addresses themselves are ignored; only the byte-rate values
    and their resulting distributions are compared.
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

    max_len = max(len(real_sorted), len(gen_sorted))

    real_sorted = np.pad(real_sorted, (0, max_len - len(real_sorted)))
    gen_sorted = np.pad(gen_sorted, (0, max_len - len(gen_sorted)))

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
    """

    # Extract top-N std inter-arrival values from SQL aggregation results
    real_topn = real_df_1.head(n)["std_iat"].to_numpy()
    gen_topn = gen_df_2.head(n)["std_iat"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_topn), len(gen_topn))
    real_topn = np.pad(real_topn, (0, max_len - len(real_topn)))
    gen_topn = np.pad(gen_topn, (0, max_len - len(gen_topn)))

    score = topn_value_distance(real_topn, gen_topn)

    real_vis = real_topn / 1e6
    gen_vis = gen_topn / 1e6

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_vis,
        gen_vis,
        "s"
    )

def flow_dstip_stateful_std_interarrival_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of standard deviations of packet inter-arrival times for destination IPs.
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
        gen_topn,
        "CV"
    )

def flow_dstip_stateful_cv_interarrival_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of coefficients of variation (CV) of packet inter-arrival times for
    destination IPs.
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
    """

    # Extract top-N average inter-arrival times from SQL aggregation results
    real_intervals = real_df_1.head(n)["avg_interval"].to_numpy()
    gen_intervals = gen_df_2.head(n)["avg_interval"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_intervals), len(gen_intervals))
    real_intervals = np.pad(real_intervals, (0, max_len - len(real_intervals)))
    gen_intervals = np.pad(gen_intervals, (0, max_len - len(gen_intervals)))

    score = topn_value_distance(real_intervals, gen_intervals)

    real_vis = real_intervals / 1e6
    gen_vis = gen_intervals / 1e6

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_vis,
        gen_vis,
        "s"
    )

def flow_ippair_stateful_avgpacketinterval_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of average packet inter-arrival times for source-destination IP pairs.
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
    """

    # Extract top-N durations from SQL aggregation results
    real_top = real_df_1.head(n)["duration"].to_numpy()
    gen_top = gen_df_2.head(n)["duration"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_top), len(gen_top))
    real_top = np.pad(real_top, (0, max_len - len(real_top)))
    gen_top = np.pad(gen_top, (0, max_len - len(gen_top)))

    score = topn_value_distance(real_top, gen_top)

    real_vis = real_top / 1e6
    gen_vis = gen_top / 1e6

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_vis,
        gen_vis,
        "s"
    )

def flow_ippair_stateful_flowduration_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of flow durations for source-destination IP pairs.
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
    """

    # Extract top-N byte rates from SQL aggregation results
    real_rates = real_df_1.head(n)["byte_rate"].to_numpy()
    gen_rates = gen_df_2.head(n)["byte_rate"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_rates), len(gen_rates))
    real_rates = np.pad(real_rates, (0, max_len - len(real_rates)))
    gen_rates = np.pad(gen_rates, (0, max_len - len(gen_rates)))

    score = topn_value_distance(real_rates, gen_rates)

    real_vis = real_rates * 1e6 / (1024 * 1024)
    gen_vis = gen_rates * 1e6  / (1024 * 1024)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_vis,
        gen_vis,
        "MB/s"
    )

def flow_ippair_stateful_byterate_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of byte rates for source-destination IP pairs.
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
    """

    # Extract top-N std inter-arrival values from SQL aggregation results
    real_topn = real_df_1.head(n)["std_iat"].to_numpy()
    gen_topn = gen_df_2.head(n)["std_iat"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_topn), len(gen_topn))
    real_topn = np.pad(real_topn, (0, max_len - len(real_topn)))
    gen_topn = np.pad(gen_topn, (0, max_len - len(gen_topn)))

    score = topn_value_distance(real_topn, gen_topn)

    real_vis = real_topn / 1e6
    gen_vis = gen_topn / 1e6

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_vis,
        gen_vis,
        "s"
    )

def flow_ippair_stateful_std_interarrival_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of standard deviations of packet inter-arrival times for
    source-destination IP pairs.
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
        gen_topn,
        "CV"
    )

def flow_ippair_stateful_cv_interarrival_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of coefficients of variation (CV) of packet inter-arrival times for
    source-destination IP pairs.
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
    """

    # Extract top-N average inter-arrival times from SQL aggregation results
    real_intervals = real_df_1.head(n)["avg_interval"].to_numpy()
    gen_intervals = gen_df_2.head(n)["avg_interval"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_intervals), len(gen_intervals))
    real_intervals = np.pad(real_intervals, (0, max_len - len(real_intervals)))
    gen_intervals = np.pad(gen_intervals, (0, max_len - len(gen_intervals)))

    score = topn_value_distance(real_intervals, gen_intervals)

    real_vis = real_intervals / 1e6
    gen_vis = gen_intervals / 1e6

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_vis,
        gen_vis,
        "s"
    )

def flow_fivetuple_stateful_avgpacketinterval_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of average packet inter-arrival times for 5-tuple flows.
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
    """

    # Extract top-N durations from SQL aggregation results
    real_top = real_df_1.head(n)["duration"].to_numpy()
    gen_top = gen_df_2.head(n)["duration"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_top), len(gen_top))
    real_top = np.pad(real_top, (0, max_len - len(real_top)))
    gen_top = np.pad(gen_top, (0, max_len - len(gen_top)))

    score = topn_value_distance(real_top, gen_top)

    real_vis = real_top / 1e6
    gen_vis = gen_top / 1e6

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_vis,
        gen_vis,
        "s"
    )

def flow_fivetuple_stateful_flowduration_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of flow durations for 5-tuple flows.
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
    """

    # Extract top-N byte rates from SQL aggregation results
    real_rates = real_df_1.head(n)["byte_rate"].to_numpy()
    gen_rates = gen_df_2.head(n)["byte_rate"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_rates), len(gen_rates))
    real_rates = np.pad(real_rates, (0, max_len - len(real_rates)))
    gen_rates = np.pad(gen_rates, (0, max_len - len(gen_rates)))

    score = topn_value_distance(real_rates, gen_rates)

    real_vis = real_rates * 1e6 / (1024 * 1024)
    gen_vis = gen_rates * 1e6 / (1024 * 1024)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_vis,
        gen_vis,
        "MB/s"
    )

def flow_fivetuple_stateful_byterate_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of byte rates for 5-tuple flows.
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
    """

    # Extract top-N std inter-arrival values from SQL aggregation results
    real_topn = real_df_1.head(n)["std_iat"].to_numpy()
    gen_topn = gen_df_2.head(n)["std_iat"].to_numpy()

    # Pad with zeros if one array is shorter
    max_len = max(len(real_topn), len(gen_topn))
    real_topn = np.pad(real_topn, (0, max_len - len(real_topn)))
    gen_topn = np.pad(gen_topn, (0, max_len - len(gen_topn)))

    score = topn_value_distance(real_topn, gen_topn)

    real_vis = real_topn / 1e6
    gen_vis = gen_topn / 1e6

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_vis,
        gen_vis,
        "s"
    )

def flow_fivetuple_stateful_std_interarrival_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of standard deviations of packet inter-arrival times for 5-tuple flows.
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
        gen_topn,
        "CV"
    )

def flow_fivetuple_stateful_cv_interarrival_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of coefficients of variation (CV) of packet inter-arrival times for
    5-tuple flows.
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