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
def flow_srcip_stateless_packet_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the packet counts
    for the top N source IPs.
    """

    # Extract top-N packet counts from SQL aggregation results
    real_counts = real_df_1["pkts"].to_numpy()[:n]
    gen_counts = gen_df_2["pkts"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_counts), len(gen_counts))
    real_counts = np.pad(real_counts, (0, max_len - len(real_counts)))
    gen_counts = np.pad(gen_counts, (0, max_len - len(gen_counts)))

    score = topn_value_distance(real_counts, gen_counts)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_counts,
        gen_counts
    )

def flow_srcip_stateless_bytes_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the total bytes
    for the top N source IPs.
    """

    real_bytes = real_df_1["bytes"].to_numpy()[:n]
    gen_bytes = gen_df_2["bytes"].to_numpy()[:n]

    max_len = max(len(real_bytes), len(gen_bytes))

    real_bytes = np.pad(real_bytes, (0, max_len - len(real_bytes)))
    gen_bytes = np.pad(gen_bytes, (0, max_len - len(gen_bytes)))

    score = topn_value_distance(real_bytes, gen_bytes)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_bytes,
        gen_bytes
    )

def flow_srcip_stateless_bytes_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of total bytes per source IP.
    """

    real_bytes = real_df_1["bytes"].to_numpy()
    gen_bytes = gen_df_2["bytes"].to_numpy()

    real_dist = (
        real_bytes / real_bytes.sum()
        if real_bytes.sum() > 0
        else np.zeros_like(real_bytes, dtype=float)
    )

    gen_dist = (
        gen_bytes / gen_bytes.sum()
        if gen_bytes.sum() > 0
        else np.zeros_like(gen_bytes, dtype=float)
    )

    max_len = max(len(real_dist), len(gen_dist))

    real_dist = np.pad(real_dist, (0, max_len - len(real_dist)))
    gen_dist = np.pad(gen_dist, (0, max_len - len(gen_dist)))

    score = jensenshannon_wrapper(real_dist, gen_dist, base=2)

    return build_distribution(
        score,
        [str(x) for x in range(max_len)],
        real_dist,
        gen_dist
    )

def flow_srcip_stateless_connection2srcport_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct source ports for the top N source IPs.
    """

    real_conn = real_df_1["n"].to_numpy()[:n]
    gen_conn = gen_df_2["n"].to_numpy()[:n]

    max_len = max(len(real_conn), len(gen_conn))

    real_conn = np.pad(real_conn, (0, max_len - len(real_conn)))
    gen_conn = np.pad(gen_conn, (0, max_len - len(gen_conn)))

    score = topn_value_distance(real_conn, gen_conn)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_conn,
        gen_conn
    )

def flow_srcip_stateless_connection2srcport_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of distinct source-port counts per source IP.
    """

    real_conn = real_df_1["n"].to_numpy()
    gen_conn = gen_df_2["n"].to_numpy()

    real_dist = (
        real_conn / real_conn.sum()
        if real_conn.sum() > 0
        else np.zeros_like(real_conn, dtype=float)
    )

    gen_dist = (
        gen_conn / gen_conn.sum()
        if gen_conn.sum() > 0
        else np.zeros_like(gen_conn, dtype=float)
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

def flow_srcip_stateless_connection2dstip_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct destination IPs contacted by the top N source IPs.
    """

    real_conn = real_df_1["n"].to_numpy()[:n]
    gen_conn = gen_df_2["n"].to_numpy()[:n]

    max_len = max(len(real_conn), len(gen_conn))

    real_conn = np.pad(real_conn, (0, max_len - len(real_conn)))
    gen_conn = np.pad(gen_conn, (0, max_len - len(gen_conn)))

    score = topn_value_distance(real_conn, gen_conn)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_conn,
        gen_conn
    )

def flow_srcip_stateless_connection2dstip_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of distinct destination-IP counts per source IP.
    """

    real_conn = real_df_1["n"].to_numpy()
    gen_conn = gen_df_2["n"].to_numpy()

    real_dist = (
        real_conn / real_conn.sum()
        if real_conn.sum() > 0
        else np.zeros_like(real_conn, dtype=float)
    )

    gen_dist = (
        gen_conn / gen_conn.sum()
        if gen_conn.sum() > 0
        else np.zeros_like(gen_conn, dtype=float)
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

def flow_srcip_stateless_connection2dstport_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct destination ports contacted by the top N source IPs.
    """

    real_conn = real_df_1["n"].to_numpy()[:n]
    gen_conn = gen_df_2["n"].to_numpy()[:n]

    max_len = max(len(real_conn), len(gen_conn))

    real_conn = np.pad(real_conn, (0, max_len - len(real_conn)))
    gen_conn = np.pad(gen_conn, (0, max_len - len(gen_conn)))

    score = topn_value_distance(real_conn, gen_conn)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_conn,
        gen_conn
    )

def flow_srcip_stateless_connection2dstport_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of distinct destination-port counts per source IP.
    """

    real_conn = real_df_1["n"].to_numpy()
    gen_conn = gen_df_2["n"].to_numpy()

    real_dist = (
        real_conn / real_conn.sum()
        if real_conn.sum() > 0
        else np.zeros_like(real_conn, dtype=float)
    )

    gen_dist = (
        gen_conn / gen_conn.sum()
        if gen_conn.sum() > 0
        else np.zeros_like(gen_conn, dtype=float)
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

def flow_srcip_stateless_connection2dstipport_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct (dstip, dstport) pairs contacted by the top N source IPs.
    """

    # Extract top-N distinct (dstip, dstport) pair counts
    real_top = real_df_1["n"].to_numpy()[:n]
    gen_top = gen_df_2["n"].to_numpy()[:n]

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

def flow_srcip_stateless_connection2dstipport_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of distinct (dstip, dstport) pair counts per source IP.
    """

    real_conn = real_df_1["n"].to_numpy()
    gen_conn = gen_df_2["n"].to_numpy()

    real_dist = (
        real_conn / real_conn.sum()
        if real_conn.sum() > 0
        else np.zeros_like(real_conn, dtype=float)
    )

    gen_dist = (
        gen_conn / gen_conn.sum()
        if gen_conn.sum() > 0
        else np.zeros_like(gen_conn, dtype=float)
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

def flow_srcip_stateless_connection2flow_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct 5-tuple flows per source IP for the top N source IPs.
    """

    # Extract top-N flow counts from SQL aggregation results
    real_top = real_df_1["n"].to_numpy()[:n]
    gen_top = gen_df_2["n"].to_numpy()[:n]

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

def flow_srcip_stateless_connection2flow_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of distinct 5-tuple flow counts per source IP.
    """

    real_counts = real_df_1["n"].to_numpy()
    gen_counts = gen_df_2["n"].to_numpy()

    real_dist = (
        real_counts / real_counts.sum()
        if real_counts.sum() > 0
        else np.zeros_like(real_counts, dtype=float)
    )

    gen_dist = (
        gen_counts / gen_counts.sum()
        if gen_counts.sum() > 0
        else np.zeros_like(gen_counts, dtype=float)
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
def flow_dstip_stateless_packet_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the packet counts
    for the top N destination IPs.
    """

    # Extract top-N packet counts from SQL aggregation results
    real_counts = real_df_1["pkts"].to_numpy()[:n]
    gen_counts = gen_df_2["pkts"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_counts), len(gen_counts))
    real_counts = np.pad(real_counts, (0, max_len - len(real_counts)))
    gen_counts = np.pad(gen_counts, (0, max_len - len(gen_counts)))

    score = topn_value_distance(real_counts, gen_counts)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_counts,
        gen_counts
    )

def flow_dstip_stateless_bytes_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the total bytes
    for the top N destination IPs.
    """

    # Extract top-N byte counts from SQL aggregation results
    real_bytes = real_df_1["bytes"].to_numpy()[:n]
    gen_bytes = gen_df_2["bytes"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_bytes), len(gen_bytes))
    real_bytes = np.pad(real_bytes, (0, max_len - len(real_bytes)))
    gen_bytes = np.pad(gen_bytes, (0, max_len - len(gen_bytes)))

    score = topn_value_distance(real_bytes, gen_bytes)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_bytes,
        gen_bytes
    )

def flow_dstip_stateless_bytes_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of total bytes per destination IP.
    """

    real_bytes = real_df_1["bytes"].to_numpy()
    gen_bytes = gen_df_2["bytes"].to_numpy()

    real_dist = (
        real_bytes / real_bytes.sum()
        if real_bytes.sum() > 0
        else np.zeros_like(real_bytes, dtype=float)
    )

    gen_dist = (
        gen_bytes / gen_bytes.sum()
        if gen_bytes.sum() > 0
        else np.zeros_like(gen_bytes, dtype=float)
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

def flow_dstip_stateless_connection2dstport_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct destination ports for the top N destination IPs.
    """

    # Extract top-N distinct destination-port counts from SQL aggregation results
    real_conn = real_df_1["n"].to_numpy()[:n]
    gen_conn = gen_df_2["n"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_conn), len(gen_conn))
    real_conn = np.pad(real_conn, (0, max_len - len(real_conn)))
    gen_conn = np.pad(gen_conn, (0, max_len - len(gen_conn)))

    score = topn_value_distance(real_conn, gen_conn)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_conn,
        gen_conn
    )

def flow_dstip_stateless_connection2dstport_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of distinct destination-port counts per destination IP.
    """

    real_conn = real_df_1["n"].to_numpy()
    gen_conn = gen_df_2["n"].to_numpy()

    real_dist = (
        real_conn / real_conn.sum()
        if real_conn.sum() > 0
        else np.zeros_like(real_conn, dtype=float)
    )

    gen_dist = (
        gen_conn / gen_conn.sum()
        if gen_conn.sum() > 0
        else np.zeros_like(gen_conn, dtype=float)
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

def flow_dstip_stateless_connection2srcip_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct source IPs contacting the top N destination IPs.
    """

    # Extract top-N distinct source-IP counts from SQL aggregation results
    real_conn = real_df_1["n"].to_numpy()[:n]
    gen_conn = gen_df_2["n"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_conn), len(gen_conn))
    real_conn = np.pad(real_conn, (0, max_len - len(real_conn)))
    gen_conn = np.pad(gen_conn, (0, max_len - len(gen_conn)))

    score = topn_value_distance(real_conn, gen_conn)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_conn,
        gen_conn
    )

def flow_dstip_stateless_connection2srcip_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of distinct source-IP counts per destination IP.
    """

    real_conn = real_df_1["n"].to_numpy()
    gen_conn = gen_df_2["n"].to_numpy()

    real_dist = (
        real_conn / real_conn.sum()
        if real_conn.sum() > 0
        else np.zeros_like(real_conn, dtype=float)
    )

    gen_dist = (
        gen_conn / gen_conn.sum()
        if gen_conn.sum() > 0
        else np.zeros_like(gen_conn, dtype=float)
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

def flow_dstip_stateless_connection2srcport_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct source ports for the top N destination IPs.
    """

    # Extract top-N distinct source-port counts from SQL aggregation results
    real_conn = real_df_1["n"].to_numpy()[:n]
    gen_conn = gen_df_2["n"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_conn), len(gen_conn))
    real_conn = np.pad(real_conn, (0, max_len - len(real_conn)))
    gen_conn = np.pad(gen_conn, (0, max_len - len(gen_conn)))

    score = topn_value_distance(real_conn, gen_conn)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_conn,
        gen_conn
    )

def flow_dstip_stateless_connection2srcport_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of distinct source-port counts per destination IP.
    """

    real_conn = real_df_1["n"].to_numpy()
    gen_conn = gen_df_2["n"].to_numpy()

    real_dist = (
        real_conn / real_conn.sum()
        if real_conn.sum() > 0
        else np.zeros_like(real_conn, dtype=float)
    )

    gen_dist = (
        gen_conn / gen_conn.sum()
        if gen_conn.sum() > 0
        else np.zeros_like(gen_conn, dtype=float)
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

def flow_dstip_stateless_connection2srcipport_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct (srcip, srcport) pairs associated with the top N destination IPs.
    """

    # Extract top-N distinct (srcip, srcport) pair counts
    real_top = real_df_1["n"].to_numpy()[:n]
    gen_top = gen_df_2["n"].to_numpy()[:n]

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

def flow_dstip_stateless_connection2srcipport_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of distinct (srcip, srcport) pair counts per destination IP.
    """

    real_conn = real_df_1["n"].to_numpy()
    gen_conn = gen_df_2["n"].to_numpy()

    real_dist = (
        real_conn / real_conn.sum()
        if real_conn.sum() > 0
        else np.zeros_like(real_conn, dtype=float)
    )

    gen_dist = (
        gen_conn / gen_conn.sum()
        if gen_conn.sum() > 0
        else np.zeros_like(gen_conn, dtype=float)
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

def flow_dstip_stateless_connection2flow_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct 5-tuple flows per destination IP for the top N destination IPs.
    """

    real_top = real_df_1["n"].to_numpy()[:n]
    gen_top = gen_df_2["n"].to_numpy()[:n]

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

def flow_dstip_stateless_connection2flow_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of distinct 5-tuple flow counts per destination IP.
    """

    real_counts = real_df_1["n"].to_numpy()
    gen_counts = gen_df_2["n"].to_numpy()

    real_dist = (
        real_counts / real_counts.sum()
        if real_counts.sum() > 0
        else np.zeros_like(real_counts, dtype=float)
    )

    gen_dist = (
        gen_counts / gen_counts.sum()
        if gen_counts.sum() > 0
        else np.zeros_like(gen_counts, dtype=float)
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
def flow_ippair_stateless_packet_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the packet counts
    for the top N source-destination IP pairs.
    """

    real_counts = real_df_1["pkts"].to_numpy()[:n]
    gen_counts = gen_df_2["pkts"].to_numpy()[:n]

    max_len = max(len(real_counts), len(gen_counts))

    real_counts = np.pad(real_counts, (0, max_len - len(real_counts)))
    gen_counts = np.pad(gen_counts, (0, max_len - len(gen_counts)))

    score = topn_value_distance(real_counts, gen_counts)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_counts,
        gen_counts
    )

def flow_ippair_stateless_packet_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the packet-count
    distributions of source-destination IP pairs.
    """

    real_counts = real_df_1["pkts"].to_numpy()
    gen_counts = gen_df_2["pkts"].to_numpy()

    real_dist = (
        real_counts / real_counts.sum()
        if real_counts.sum() > 0
        else np.zeros_like(real_counts, dtype=float)
    )

    gen_dist = (
        gen_counts / gen_counts.sum()
        if gen_counts.sum() > 0
        else np.zeros_like(gen_counts, dtype=float)
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

def flow_ippair_stateless_bytes_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the total bytes
    for the top N source-destination IP pairs.
    """

    # Extract top-N byte counts from SQL aggregation results
    real_bytes = real_df_1["bytes"].to_numpy()[:n]
    gen_bytes = gen_df_2["bytes"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_bytes), len(gen_bytes))
    real_bytes = np.pad(real_bytes, (0, max_len - len(real_bytes)))
    gen_bytes = np.pad(gen_bytes, (0, max_len - len(gen_bytes)))

    score = topn_value_distance(real_bytes, gen_bytes)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_bytes,
        gen_bytes
    )

def flow_ippair_stateless_bytes_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the byte-count
    distributions of source-destination IP pairs.
    """

    real_bytes = real_df_1["bytes"].to_numpy()
    gen_bytes = gen_df_2["bytes"].to_numpy()

    real_dist = (
        real_bytes / real_bytes.sum()
        if real_bytes.sum() > 0
        else np.zeros_like(real_bytes, dtype=float)
    )

    gen_dist = (
        gen_bytes / gen_bytes.sum()
        if gen_bytes.sum() > 0
        else np.zeros_like(gen_bytes, dtype=float)
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

def flow_ippair_stateless_connection2srcport_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct source ports for the top N source-destination IP pairs.
    """

    real_top = real_df_1["n"].to_numpy()[:n]
    gen_top = gen_df_2["n"].to_numpy()[:n]

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

def flow_ippair_stateless_connection2srcport_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of distinct source-port counts per source-destination IP pair.
    """

    real_conn = real_df_1["n"].to_numpy()
    gen_conn = gen_df_2["n"].to_numpy()

    real_dist = (
        real_conn / real_conn.sum()
        if real_conn.sum() > 0
        else np.zeros_like(real_conn, dtype=float)
    )

    gen_dist = (
        gen_conn / gen_conn.sum()
        if gen_conn.sum() > 0
        else np.zeros_like(gen_conn, dtype=float)
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

def flow_ippair_stateless_connection2dstport_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct destination ports for the top N source-destination IP pairs.
    """

    # Extract top-N distinct destination-port counts from SQL aggregation results
    real_top = real_df_1["n"].to_numpy()[:n]
    gen_top = gen_df_2["n"].to_numpy()[:n]

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

def flow_ippair_stateless_connection2dstport_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of distinct destination-port counts per source-destination IP pair.
    """

    real_conn = real_df_1["n"].to_numpy()
    gen_conn = gen_df_2["n"].to_numpy()

    real_dist = (
        real_conn / real_conn.sum()
        if real_conn.sum() > 0
        else np.zeros_like(real_conn, dtype=float)
    )

    gen_dist = (
        gen_conn / gen_conn.sum()
        if gen_conn.sum() > 0
        else np.zeros_like(gen_conn, dtype=float)
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

def flow_ippair_stateless_connection2flow_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct 5-tuple flows for the top N source-destination IP pairs.
    """

    # Extract top-N flow counts from SQL aggregation results
    real_top = real_df_1["n"].to_numpy()[:n]
    gen_top = gen_df_2["n"].to_numpy()[:n]

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

def flow_ippair_stateless_connection2flow_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distributions
    of distinct 5-tuple flow counts per source-destination IP pair.
    """

    real_conn = real_df_1["n"].to_numpy()
    gen_conn = gen_df_2["n"].to_numpy()

    real_dist = (
        real_conn / real_conn.sum()
        if real_conn.sum() > 0
        else np.zeros_like(real_conn, dtype=float)
    )

    gen_dist = (
        gen_conn / gen_conn.sum()
        if gen_conn.sum() > 0
        else np.zeros_like(gen_conn, dtype=float)
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
def flow_fivetuple_stateless_packet_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the packet counts
    for the top N 5-tuple flows.
    """

    # Extract top-N packet counts from SQL aggregation results
    real_counts = real_df_1["pkts"].to_numpy()[:n]
    gen_counts = gen_df_2["pkts"].to_numpy()[:n]

    # Pad with zeros if one array is shorter
    max_len = max(len(real_counts), len(gen_counts))
    
    real_counts = np.pad(real_counts, (0, max_len - len(real_counts)))
    gen_counts = np.pad(gen_counts, (0, max_len - len(gen_counts)))

    score = topn_value_distance(real_counts, gen_counts)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_counts,
        gen_counts
    )

def flow_fivetuple_stateless_packet_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between packet-count
    distributions of 5-tuple flows.
    """

    real_counts = real_df_1["pkts"].to_numpy()
    gen_counts = gen_df_2["pkts"].to_numpy()

    real_dist = (
        real_counts / real_counts.sum()
        if real_counts.sum() > 0
        else np.zeros_like(real_counts, dtype=float)
    )

    gen_dist = (
        gen_counts / gen_counts.sum()
        if gen_counts.sum() > 0
        else np.zeros_like(gen_counts, dtype=float)
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

def flow_fivetuple_stateless_bytes_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the total bytes
    for the top N 5-tuple flows.
    """

    # Extract top-N byte counts from SQL aggregation results
    real_bytes = real_df_1["bytes"].to_numpy()[:n]
    gen_bytes = gen_df_2["bytes"].to_numpy()[:n]
    
    # Pad with zeros if one array is shorter
    max_len = max(len(real_bytes), len(gen_bytes))
    
    real_bytes = np.pad(real_bytes, (0, max_len - len(real_bytes)))
    gen_bytes = np.pad(gen_bytes, (0, max_len - len(gen_bytes)))

    score = topn_value_distance(real_bytes, gen_bytes)

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_bytes,
        gen_bytes
    )

def flow_fivetuple_stateless_bytes_distribution(real_df_1, gen_df_2):
    """
    Computes the Jensen-Shannon Divergence (JSD) between byte-count
    distributions of 5-tuple flows.
    """

    real_bytes = real_df_1["bytes"].to_numpy()
    gen_bytes = gen_df_2["bytes"].to_numpy()

    real_dist = (
        real_bytes / real_bytes.sum()
        if real_bytes.sum() > 0
        else np.zeros_like(real_bytes, dtype=float)
    )

    gen_dist = (
        gen_bytes / gen_bytes.sum()
        if gen_bytes.sum() > 0
        else np.zeros_like(gen_bytes, dtype=float)
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