import sys
import os
import math
import pandas as pd
import numpy as np
from scipy.spatial.distance import jensenshannon
from scipy.stats import wasserstein_distance
from tqdm import tqdm


def sample_rank_distribution(max_len: int, n_points: int = 500):
    """
    Generate logarithmically spaced indices for visualization
    while preserving detail in the distribution head.

    Parameters
    ----------
    max_len : int
        Length of the full ranked distribution.
    n_points : int
        Maximum number of visualization points.

    Returns
    -------
    np.ndarray
        Sorted unique indices.
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

def build_topn(score, labels, real, synthetic):

    return {
        "score": round(float(score), 4),

        "visualization": {
            "type": "topn",
            "labels": list(labels),
            "real": [float(x) for x in real],
            "synthetic": [float(x) for x in synthetic]
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
    ----------
    vis_df : pd.DataFrame
        DataFrame containing aligned visualization data.

    x_col : str
        Ordered numeric axis column
        (bucket, len_bucket, duration_bucket, etc.)

    real_col : str
        Real distribution column.

    synthetic_col : str
        Synthetic distribution column.

    n_points : int
        Maximum points to return.

    Returns
    -------
    pd.DataFrame
        Downsampled dataframe suitable for line charts.
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


# Global Packet Statistics
def packet_stateless__count(real_df_1, gen_df_2, n=10):
    """
    Computes the Absolute Relative Error (ARE) of the total number of packets
    between the real and generated datasets.
    """

    real_count = int(real_df_1["total_packets"].iloc[0])
    gen_count = int(gen_df_2["total_packets"].iloc[0])

    if real_count == 0:
        score = 1.0 if gen_count > 0 else 0.0
    else:
        score = min(
            abs(real_count - gen_count) / real_count,
            1.0
        )

    return {
        "score": round(float(score), 4),

        "visualization": {
            "type": "dual_bar",
            "label": "Total Packets",
            "real": real_count,
            "synthetic": gen_count
        }
    }

def packet_stateless_srcip_countdistinct(real_df_1, gen_df_2, n=10):
    """
    Computes the Absolute Relative Error (ARE) of the number of distinct
    source IPs between the real and generated datasets.
    """

    real_count = int(real_df_1["n_src_ips"].iat[0])
    gen_count = int(gen_df_2["n_src_ips"].iat[0])

    if real_count == 0:
        score = 1.0 if gen_count > 0 else 0.0
    else:
        score = min(
            abs(real_count - gen_count) / real_count,
            1.0
        )

    return {
        "score": round(float(score), 4),

        "visualization": {
            "type": "dual_bar",
            "label": "Distinct Source IPs",
            "real": real_count,
            "synthetic": gen_count
        }
    }

def packet_stateless_srcip_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the source IP packet
    distributions of the real and generated datasets. The comparison is IP-agnostic
    and uses the packet-count distribution returned by SQL aggregation.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcip, COUNT(*) AS pkts
        FROM <table_name>
        GROUP BY srcip
        ORDER BY pkts DESC

        Therefore, each DataFrame contains one row per source IP with
        the aggregated packet count in the 'pkts' column.
    """

    # Extract packet counts per source IP from SQL aggregation results
    real_counts = real_df_1["pkts"].to_numpy()
    gen_counts = gen_df_2["pkts"].to_numpy()

    
    # Normalize to obtain relative distributions
    real_dist = real_counts / real_counts.sum()
    gen_dist = gen_counts / gen_counts.sum()
    
    # Sort distributions in descending order (IP-agnostic)
    real_dist_sorted = np.sort(real_dist)[::-1]
    gen_dist_sorted = np.sort(gen_dist)[::-1]
    
    # Pad the shorter array with zeros
    max_len = max(len(real_dist_sorted), len(gen_dist_sorted))
    real_padded = np.pad(real_dist_sorted, (0, max_len - len(real_dist_sorted)))
    gen_padded = np.pad(gen_dist_sorted, (0, max_len - len(gen_dist_sorted)))
    
    # Compute and return JSD
    score = jensenshannon_wrapper(
        real_padded,
        gen_padded,
        base=2
    )

    # Separate visualization sampling
    vis_idx = sample_rank_distribution(max_len)

    return {
        "score": round(float(score), 4),

        "visualization": {
            "type": "distribution",
            "ranks": (vis_idx + 1).tolist(),
            "real": real_padded[vis_idx].tolist(),
            "synthetic": gen_padded[vis_idx].tolist()
        }
    }

def packet_stateless_dstip_countdistinct(real_df_1, gen_df_2, n=10):
    """
    Computes the Absolute Relative Error (ARE) of the number of distinct
    destination IPs between the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT COUNT(DISTINCT dstip) AS n_dst_ips
        FROM <table_name>

        Therefore, each DataFrame contains a single row with the
        'n_dst_ips' column instead of raw packet-level records.
    """

    # Extract distinct destination IP counts from the SQL aggregation results
    real_count = int(real_df_1["n_dst_ips"].iloc[0])
    gen_count = int(gen_df_2["n_dst_ips"].iloc[0])

    if real_count == 0:
        score = 1.0 if gen_count > 0 else 0.0
    else:
        score = min(
            abs(real_count - gen_count) / real_count,
            1.0
        )

    return {
        "score": round(float(score), 4),

        "visualization": {
            "type": "dual_bar",
            "label": "Distinct Destination IPs",
            "real": real_count,
            "synthetic": gen_count
        }
    }

def packet_stateless_dstip_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the destination IP
    packet distributions of the real and generated datasets. The comparison
    is IP-agnostic and uses the packet-count distribution returned by SQL
    aggregation.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstip, COUNT(*) AS pkts
        FROM <table_name>
        GROUP BY dstip
        ORDER BY pkts DESC

        Therefore, each DataFrame contains one row per destination IP with
        the aggregated packet count in the 'pkts' column.
    """

    # Extract packet counts per destination IP from SQL aggregation results
    real_counts = real_df_1["pkts"].to_numpy()
    gen_counts = gen_df_2["pkts"].to_numpy()

    # Normalize to obtain relative distributions
    real_dist = real_counts / real_counts.sum()
    gen_dist = gen_counts / gen_counts.sum()

    # Sort distributions in descending order (IP-agnostic)
    real_dist_sorted = np.sort(real_dist)[::-1]
    gen_dist_sorted = np.sort(gen_dist)[::-1]

    # Pad the shorter array with zeros to match lengths
    max_len = max(len(real_dist_sorted), len(gen_dist_sorted))
    real_padded = np.pad(real_dist_sorted, (0, max_len - len(real_dist_sorted)))
    gen_padded = np.pad(gen_dist_sorted, (0, max_len - len(gen_dist_sorted)))

    # Compute and return JSD
    score = jensenshannon_wrapper(
        real_padded,
        gen_padded,
        base=2
    )

    vis_idx = sample_rank_distribution(max_len)

    return {
        "score": round(float(score), 4),

        "visualization": {
            "type": "distribution",
            "ranks": (vis_idx + 1).tolist(),
            "real": real_padded[vis_idx].tolist(),
            "synthetic": gen_padded[vis_idx].tolist()
        }
    }

def packet_stateless_srcport_countdistinct(real_df_1, gen_df_2, n=10):
    """
    Computes the Absolute Relative Error (ARE) of the number of distinct
    source ports between the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT COUNT(DISTINCT srcport) AS n_src_ports
        FROM <table_name>

        Therefore, each DataFrame contains a single row with the
        'n_src_ports' column instead of raw packet-level records.
    """

    # Extract distinct source port counts from the SQL aggregation results
    real_count = int(real_df_1["n_src_ports"].iloc[0])
    gen_count = int(gen_df_2["n_src_ports"].iloc[0])

    if real_count == 0:
        return 1.0 if gen_count > 0 else 0.0

    # Absolute Relative Error (ARE)
    error = abs(real_count - gen_count) / real_count
    score = min(error, 1.0)

    return {
        "score": round(float(score), 4),

        "visualization": {
            "type": "dual_bar",
            "label": "Distinct Source Ports",
            "real": real_count,
            "synthetic": gen_count
        }
    }

def packet_stateless_srcport_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the source port
    distributions of the real and generated datasets. This comparison is
    port-specific (not agnostic).

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, COUNT(*) AS pkts
        FROM <table_name>
        GROUP BY srcport

        Therefore, each DataFrame contains one row per source port with
        the aggregated packet count in the 'pkts' column.
    """

    # Normalize packet counts returned by SQL
    real_dist = (real_df_1.set_index("srcport")["pkts"] / real_df_1["pkts"].sum())
    gen_dist = (gen_df_2.set_index("srcport")["pkts"] / gen_df_2["pkts"].sum())

    # Align indices to ensure both have the same port list
    all_ports = set(real_dist.index).union(set(gen_dist.index))
    real_aligned = real_dist.reindex(all_ports, fill_value=0).sort_index()
    gen_aligned = gen_dist.reindex(all_ports, fill_value=0).sort_index()

    # Compute and return JSD
    score = jensenshannon_wrapper(
        real_aligned.values,
        gen_aligned.values,
        base=2
    )

    vis_df = pd.DataFrame({
        "port": real_aligned.index,
        "real": real_aligned.values,
        "synthetic": gen_aligned.values,
    })

    vis_df["importance"] = np.maximum(
        vis_df["real"],
        vis_df["synthetic"]
    )

    vis_df = vis_df.sort_values(
        "importance",
        ascending=False
    ).head(20)

    return {
        "score": round(float(score), 4),

        "visualization": {
            "type": "grouped_bar",
            "labels": vis_df["port"].astype(str).tolist(),
            "real": vis_df["real"].tolist(),
            "synthetic": vis_df["synthetic"].tolist()
        }
    }

def packet_stateless_dstport_countdistinct(real_df_1, gen_df_2, n=10):
    """
    Computes the Absolute Relative Error (ARE) of the number of distinct
    destination ports between the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT COUNT(DISTINCT dstport) AS n_dst_ports
        FROM <table_name>

        Therefore, each DataFrame contains a single row with the
        'n_dst_ports' column instead of raw packet-level records.
    """

    # Extract distinct destination port counts from the SQL aggregation results
    real_count = int(real_df_1["n_dst_ports"].iloc[0])
    gen_count = int(gen_df_2["n_dst_ports"].iloc[0])

    if real_count == 0:
        score = 1.0 if gen_count > 0 else 0.0
    else:
        score = min(
            abs(real_count - gen_count) / real_count,
            1.0
        )

    return {
        "score": round(float(score), 4),
        
        "visualization": {
            "type": "dual_bar",
            "label": "Distinct Destination Ports",
            "real": real_count,
            "synthetic": gen_count
        }
    }

def packet_stateless_dstport_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the destination port
    distributions of the real and generated datasets. This comparison is
    port-specific (not agnostic).

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport, COUNT(*) AS pkts
        FROM <table_name>
        GROUP BY dstport

        Therefore, each DataFrame contains one row per destination port with
        the aggregated packet count in the 'pkts' column.
    """

    # Normalize packet counts returned by SQL
    real_dist = (real_df_1.set_index("dstport")["pkts"] / real_df_1["pkts"].sum())
    gen_dist = (gen_df_2.set_index("dstport")["pkts"] / gen_df_2["pkts"].sum())

    # Align indices to ensure both have the same set of ports
    all_ports = set(real_dist.index).union(set(gen_dist.index))
    real_aligned = real_dist.reindex(all_ports, fill_value=0).sort_index()
    gen_aligned = gen_dist.reindex(all_ports, fill_value=0).sort_index()

    # Compute and return JSD
    score = jensenshannon_wrapper(real_aligned.values, gen_aligned.values, base=2)

    vis_df = pd.DataFrame({
        "port": real_aligned.index,
        "real": real_aligned.values,
        "synthetic": gen_aligned.values,
    })

    # show most important ports
    vis_df["importance"] = np.maximum(
        vis_df["real"],
        vis_df["synthetic"]
    )

    vis_df = (
        vis_df
        .sort_values("importance", ascending=False)
        .head(20)
    )

    return {
        "score": round(float(score), 4),

        "visualization": {
            "type": "grouped_bar",
            "labels": vis_df["port"].astype(str).tolist(),
            "real": vis_df["real"].tolist(),
            "synthetic": vis_df["synthetic"].tolist()
        }
    }

def packet_stateless_proto_countdistinct(real_df_1, gen_df_2, n=10):
    """
    Computes the Absolute Relative Error (ARE) of the number of distinct
    protocols between the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT COUNT(DISTINCT proto) AS n_protocols
        FROM <table_name>

        Therefore, each DataFrame contains a single row with the
        'n_protocols' column instead of raw packet-level records.
    """

    # Extract distinct protocol counts from the SQL aggregation results
    real_count = int(real_df_1["n_protocols"].iloc[0])
    gen_count = int(gen_df_2["n_protocols"].iloc[0])

    if real_count == 0:
        score = 1.0 if gen_count > 0 else 0.0
    else:
        score = min(
            abs(real_count - gen_count) / real_count,
            1.0
        )

    return build_single_value(
        score=score,
        label="Distinct Protocols",
        real=real_count,
        synthetic=gen_count
    )

def packet_stateless_proto_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the protocol
    distributions of the real and generated datasets. This comparison is
    protocol-specific (not agnostic).

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT proto, COUNT(*) AS pkts
        FROM <table_name>
        GROUP BY proto

        Therefore, each DataFrame contains one row per protocol with
        the aggregated packet count in the 'pkts' column.
    """

    # Normalize packet counts returned by SQL
    real_dist = (
        real_df_1.set_index("proto")["pkts"] / real_df_1["pkts"].sum()
    )

    gen_dist = (
        gen_df_2.set_index("proto")["pkts"] / gen_df_2["pkts"].sum()
    )

    # Align indices to ensure both have the same set of protocols
    all_protocols = set(real_dist.index).union(set(gen_dist.index))
    real_aligned = real_dist.reindex(all_protocols, fill_value=0).sort_index()
    gen_aligned = gen_dist.reindex(all_protocols, fill_value=0).sort_index()

    # Compute and return JSD
    score = jensenshannon_wrapper(real_aligned.values, gen_aligned.values, base=2)
    
    vis_df = pd.DataFrame({
        "protocol": real_aligned.index,
        "real": real_aligned.values,
        "synthetic": gen_aligned.values,
    })

    vis_df["importance"] = np.maximum(
        vis_df["real"],
        vis_df["synthetic"]
    )

    vis_df = vis_df.sort_values(
        "importance",
        ascending=False
    )

    return {
        "score": round(float(score), 4),

        "visualization": {
            "type": "grouped_bar",
            "labels": vis_df["protocol"].astype(str).tolist(),
            "real": vis_df["real"].tolist(),
            "synthetic": vis_df["synthetic"].tolist()
        }
    }

def packet_stateless_time_distribution(real_df_1, gen_df_2, n=10):
    """
        Packet timestamp distribution.

        Implementation note:
        To reduce computational cost, timestamps are first bucketed
        into 1-second intervals in SQL. Wasserstein distance is then
        computed on the weighted bucket distribution rather than on
        individual packet timestamps.

        This is an approximation of the original metric and was
        validated to produce equivalent scores on benchmark datasets.
    """

    real_positions = real_df_1["bucket"].to_numpy(dtype=float)
    gen_positions = gen_df_2["bucket"].to_numpy(dtype=float)

    # Normalize bucket positions jointly
    all_positions = np.concatenate([real_positions, gen_positions])

    min_pos = all_positions.min()
    max_pos = all_positions.max()

    if max_pos > min_pos:
        real_positions = (real_positions - min_pos) / (max_pos - min_pos)
        gen_positions = (gen_positions - min_pos) / (max_pos - min_pos)
    else:
        real_positions = real_positions * 0
        gen_positions = gen_positions * 0

    real_weights = real_df_1["pkts"].to_numpy(dtype=float)
    gen_weights = gen_df_2["pkts"].to_numpy(dtype=float)

    real_weights /= real_weights.sum()
    gen_weights /= gen_weights.sum()

    score = wasserstein_distance(
        real_positions,
        gen_positions,
        u_weights=real_weights,
        v_weights=gen_weights,
    )

    # Visualization data
    real_dist = (
        real_df_1.set_index("bucket")["pkts"]
        / real_df_1["pkts"].sum()
    )

    gen_dist = (
        gen_df_2.set_index("bucket")["pkts"]
        / gen_df_2["pkts"].sum()
    )

    # Align buckets
    all_buckets = sorted(
        set(real_dist.index).union(gen_dist.index)
    )

    real_aligned = real_dist.reindex(
        all_buckets,
        fill_value=0
    )

    gen_aligned = gen_dist.reindex(
        all_buckets,
        fill_value=0
    )

    vis_df = pd.DataFrame({
        "bucket": all_buckets,
        "real": real_aligned.values,
        "synthetic": gen_aligned.values,
    })

    vis_df["bucket"] = (
        vis_df["bucket"] - vis_df["bucket"].min()
    ) / 3600

    # Downsample only for visualization
    vis_df = downsample_numeric_distribution(
        vis_df=vis_df,
        x_col="bucket",
        real_col="real",
        synthetic_col="synthetic",
        n_points=50
    )

    return {
        "score": round(float(score), 4),
        "visualization": {
            "type": "overlay_line",
            "labels": [
                str(round(x, 2))
                for x in vis_df["bucket"]
            ],
            "real": vis_df["real"].tolist(),
            "synthetic": vis_df["synthetic"].tolist(),
        }
    }

def packet_stateless_pktlen_sum(real_df_1, gen_df_2, n=10):
    """
    Computes the Absolute Relative Error (ARE) between the total packet lengths
    of the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT SUM(pkt_len) AS total_bytes
        FROM <table_name>

        Therefore, each DataFrame contains a single row with the
        'total_bytes' column.
    """

    # Extract total packet bytes from SQL aggregation results
    real_sum = float(real_df_1["total_bytes"].iloc[0])
    gen_sum = float(gen_df_2["total_bytes"].iloc[0])

    if real_sum == 0:
        score = 1.0 if gen_sum > 0 else 0.0
    else:
        score = min(abs(real_sum - gen_sum) / real_sum, 1.0)

    return build_single_value(
        score=score,
        label="Total Packet Length",
        real=real_sum,
        synthetic=gen_sum
    )

def packet_stateless_pktlen_avg(real_df_1, gen_df_2, n=10):
    """
    Computes the Absolute Relative Error (ARE) between the average packet lengths
    of the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT AVG(pkt_len) AS avg_pkt_len
        FROM <table_name>

        Therefore, each DataFrame contains a single row with the
        'avg_pkt_len' column.
    """

    # Extract average packet lengths from SQL aggregation results
    real_avg = float(real_df_1["avg_pkt_len"].iloc[0])
    gen_avg = float(gen_df_2["avg_pkt_len"].iloc[0])

    if real_avg == 0:
        score = 1.0 if gen_avg > 0 else 0.0
    else:
        score = min(abs(real_avg - gen_avg) / real_avg, 1.0)

    return build_single_value(
        score=score,
        label="Average Packet Length",
        real=real_avg,
        synthetic=gen_avg
    )

def packet_stateless_pktlen_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between packet length
    distributions of the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT
            CAST(FLOOR(pkt_len / 1) * 1 AS INT) AS len_bucket,
            COUNT(*) AS pkts
        FROM <table_name>
        GROUP BY len_bucket
        ORDER BY len_bucket

        This creates 1-byte packet-length buckets and returns the
        packet count for each bucket. The counts are converted to
        probability distributions and compared using JSD.

    Returns:
        float: Jensen-Shannon Divergence (JSD) value in [0, 1].
    """

    # Convert packet-length bucket counts returned by SQL into probability distributions
    real_dist = (
    real_df_1.set_index("len_bucket")["pkts"] / real_df_1["pkts"].sum()
    )

    gen_dist = (
        gen_df_2.set_index("len_bucket")["pkts"] / gen_df_2["pkts"].sum()
    )

    # Align packet lengths
    all_lengths = set(real_dist.index).union(set(gen_dist.index))

    real_aligned = real_dist.reindex(all_lengths, fill_value=0).sort_index()
    gen_aligned = gen_dist.reindex(all_lengths, fill_value=0).sort_index()

    score = jensenshannon_wrapper(real_aligned.values, gen_aligned.values)

    vis_df = pd.DataFrame({
        "len_bucket": real_aligned.index,
        "real": real_aligned.values,
        "synthetic": gen_aligned.values,
    })

    vis_df = downsample_numeric_distribution(
        vis_df=vis_df,
        x_col="len_bucket",
        real_col="real",
        synthetic_col="synthetic",
        n_points=50
    )
    
    return {
        "score": round(float(score), 4),
        "visualization": {
            "type": "overlay_line",
            "x_axis_label": "Packet Length (Bytes)",
            "labels": [
                str(int(x))
                for x in vis_df["len_bucket"]
            ],
            "real": vis_df["real"].tolist(),
            "synthetic": vis_df["synthetic"].tolist(),
        }
    }


# Per Source Port Aggregations
def flow_srcport_stateless_packet_topnkey(real_df_1, gen_df_2, n=10):
    """
    Computes the 1-hit rate between the top-N source ports (by packet count)
    in the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, COUNT(*) AS pkts
        FROM <table_name>
        GROUP BY srcport
        ORDER BY pkts DESC

        Therefore, each DataFrame contains one row per source port with
        the aggregated packet count in the 'pkts' column.
    """

    # Extract top-N source ports from SQL aggregation results
    real_ports = set(real_df_1.head(n)["srcport"])
    gen_ports = set(gen_df_2.head(n)["srcport"])

    # Compute how many of the real top ports are in the generated top ports
    hits = len(real_ports.intersection(gen_ports))

    score = 1 - hits / n

    return {
        "score": round(float(score), 4),

        "visualization": {
            "type": "topnkey",

            "real": [str(x) for x in real_ports],
            "synthetic": [str(x) for x in gen_ports]
        }
    }

def flow_srcport_stateless_packet_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the packet counts
    for the top N source ports between the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, COUNT(*) AS pkts
        FROM <table_name>
        GROUP BY srcport
        ORDER BY pkts DESC

        Therefore, each DataFrame contains one row per source port with
        the aggregated packet count in the 'pkts' column.
    """

    # Extract top-N packet counts from SQL aggregation results
    real_counts = real_df_1.head(n)["pkts"].to_numpy()
    gen_counts = gen_df_2.head(n)["pkts"].to_numpy()

    # Pad to the same length
    max_len = max(len(real_counts), len(gen_counts))
    real_counts = np.pad(real_counts, (0, max_len - len(real_counts)))
    gen_counts = np.pad(gen_counts, (0, max_len - len(gen_counts)))

    score = topn_value_distance(
        real_counts,
        gen_counts
    )

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_counts,
        gen_counts
    )

def flow_srcport_stateless_bytes_topnkey(real_df_1, gen_df_2, n=10):
    """
    Computes the 1-hit rate between the top-N source ports (by total bytes sent)
    in the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, SUM(pkt_len) AS bytes
        FROM <table_name>
        GROUP BY srcport
        ORDER BY bytes DESC

        Therefore, each DataFrame contains one row per source port with
        the aggregated byte count in the 'bytes' column and is already
        sorted in descending order of total bytes.

    Returns:
        float: 1-hit rate (recall@N) between real and generated top-N
        source ports by byte volume.
    """

    # SQL already returns rows ordered by bytes DESC
    real_top_ports = set(real_df_1.head(n)["srcport"])
    gen_top_ports = set(gen_df_2.head(n)["srcport"])

    hits = len(real_top_ports.intersection(gen_top_ports))

    score = 1 - hits / n

    return {
        "score": round(float(score), 4),

        "visualization": {
            "type": "topnkey",
            "real": [str(x) for x in real_top_ports],
            "synthetic": [str(x) for x in gen_top_ports]
        }
    }

def flow_srcport_stateless_bytes_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the total bytes
    sent by the top N source ports between the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, SUM(pkt_len) AS bytes
        FROM <table_name>
        GROUP BY srcport
        ORDER BY bytes DESC

        Therefore, each DataFrame contains one row per source port with
        the aggregated byte count in the 'bytes' column.
    """

    # Extract top-N byte counts from SQL aggregation results
    real_bytes = real_df_1.head(n)["bytes"].to_numpy()
    gen_bytes = gen_df_2.head(n)["bytes"].to_numpy()

    # Pad to the same length
    max_len = max(len(real_bytes), len(gen_bytes))
    real_bytes = np.pad(real_bytes, (0, max_len - len(real_bytes)))
    gen_bytes = np.pad(gen_bytes, (0, max_len - len(gen_bytes)))

    score = topn_value_distance(
        real_bytes,
        gen_bytes
    )

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_bytes,
        gen_bytes
    )

def flow_srcport_stateless_bytes_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the byte
    distributions of source ports in the real and generated datasets.
    This comparison is port-specific (not agnostic).

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, SUM(pkt_len) AS bytes
        FROM <table_name>
        GROUP BY srcport
        ORDER BY bytes DESC

        Therefore, each DataFrame contains one row per source port with
        the aggregated byte count in the 'bytes' column.

        The byte counts are normalized into probability distributions
        and aligned by source port before computing JSD.

    Returns:
        float: Jensen-Shannon Divergence (JSD) value in [0, 1].
    """

    # Normalize byte counts returned by SQL
    real_dist = (real_df_1.set_index("srcport")["bytes"] / real_df_1["bytes"].sum())

    gen_dist = (gen_df_2.set_index("srcport")["bytes"] / gen_df_2["bytes"].sum())

    # Align distributions by source port
    all_ports = set(real_dist.index).union(set(gen_dist.index))

    real_aligned = real_dist.reindex(all_ports, fill_value=0).sort_index()
    gen_aligned = gen_dist.reindex(all_ports, fill_value=0).sort_index()

    score = jensenshannon_wrapper(
        real_aligned.values,
        gen_aligned.values,
        base=2
    )

    return build_distribution(
        score,
        [str(x) for x in all_ports],
        real_aligned.values,
        gen_aligned.values
    )

def flow_srcport_stateless_connection2srcip_topnkey(real_df_1, gen_df_2, n=10):
    """
    Computes the 1-hit rate between the top-N source ports (by number of
    distinct source IPs) in the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, COUNT(DISTINCT srcip) AS n
        FROM <table_name>
        GROUP BY srcport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per source port with
        the distinct source IP count in the 'n' column and is already
        sorted in descending order of distinct source IP count.

    Returns:
        float: 1 - hit rate between real and generated top-N source ports.
    """

    real_top_ports = set(real_df_1.head(n)["srcport"])
    gen_top_ports = set(gen_df_2.head(n)["srcport"])

    hits = len(real_top_ports.intersection(gen_top_ports))

    score = 1 - hits / n

    return build_topnkey(
        score,
        real_top_ports,
        gen_top_ports
    )

def flow_srcport_stateless_connection2srcip_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct source IPs associated with the top N source ports.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, COUNT(DISTINCT srcip) AS n
        FROM <table_name>
        GROUP BY srcport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per source port with
        the distinct source IP count in the 'n' column.
    """

    # Extract top-N distinct source IP counts from SQL aggregation results
    real_conn = real_df_1.head(n)["n"].to_numpy()
    gen_conn = gen_df_2.head(n)["n"].to_numpy()

    # Pad to equal length
    max_len = max(len(real_conn), len(gen_conn))
    real_conn = np.pad(real_conn, (0, max_len - len(real_conn)))
    gen_conn = np.pad(gen_conn, (0, max_len - len(gen_conn)))

    score = topn_value_distance(
        real_conn,
        gen_conn
    )

    return build_topn(
        score,
        [f"Rank {i+1}" for i in range(max_len)],
        real_conn,
        gen_conn
    )

def flow_srcport_stateless_connection2srcip_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distribution
    of distinct source IP counts per source port in the real and generated
    datasets. The comparison is port-specific (not agnostic).

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, COUNT(DISTINCT srcip) AS n
        FROM <table_name>
        GROUP BY srcport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per source port with
        the distinct source IP count stored in the 'n' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) value in [0, 1].
    """

    real_dist = (real_df_1.set_index("srcport")["n"] / real_df_1["n"].sum())

    gen_dist = (gen_df_2.set_index("srcport")["n"] / gen_df_2["n"].sum())

    all_ports = set(real_dist.index).union(set(gen_dist.index))

    real_aligned = real_dist.reindex(all_ports, fill_value=0).sort_index()
    gen_aligned = gen_dist.reindex(all_ports, fill_value=0).sort_index()

    score = jensenshannon_wrapper(real_aligned.values, gen_aligned.values, base=2)

    return build_distribution(
        score,
        [str(x) for x in all_ports],
        real_aligned.values,
        gen_aligned.values
    )

def flow_srcport_stateless_connection2dstip_topnkey(real_df_1, gen_df_2, n=10):
    """
    Computes the 1-hit rate between the top-N source ports (by number of
    distinct destination IPs) in the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, COUNT(DISTINCT dstip) AS n
        FROM <table_name>
        GROUP BY srcport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per source port with
        the distinct destination IP count in the 'n' column and is already
        sorted in descending order of distinct destination IP count.

    Returns:
        float: 1 - hit rate between real and generated top-N source ports.
    """

    # SQL already returns rows ordered by n DESC
    real_top_ports = set(real_df_1.head(n)["srcport"])
    gen_top_ports = set(gen_df_2.head(n)["srcport"])

    hits = len(real_top_ports.intersection(gen_top_ports))

    score = 1 - hits / n

    return build_topnkey(
        score,
        real_top_ports,
        gen_top_ports
    )

def flow_srcport_stateless_connection2dstip_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct destination IPs associated with the top N source ports.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, COUNT(DISTINCT dstip) AS n
        FROM <table_name>
        GROUP BY srcport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per source port with
        the distinct destination IP count in the 'n' column.
    """

    import numpy as np

    # Extract top-N distinct destination IP counts from SQL aggregation results
    real_conn = real_df_1.head(n)["n"].to_numpy()
    gen_conn = gen_df_2.head(n)["n"].to_numpy()

    # Pad with zeros to equal length
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

def flow_srcport_stateless_connection2dstip_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distribution
    of distinct destination IP counts per source port in the real and
    generated datasets. The comparison is port-specific (not agnostic).

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, COUNT(DISTINCT dstip) AS n
        FROM <table_name>
        GROUP BY srcport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per source port with
        the distinct destination IP count stored in the 'n' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) value in [0, 1].
    """

    # Normalize distinct destination IP counts returned by SQL
    real_dist = (real_df_1.set_index("srcport")["n"] / real_df_1["n"].sum())

    gen_dist = (gen_df_2.set_index("srcport")["n"] / gen_df_2["n"].sum())

    # Align distributions by source port
    all_ports = set(real_dist.index).union(set(gen_dist.index))

    real_aligned = real_dist.reindex(all_ports, fill_value=0).sort_index()
    gen_aligned = gen_dist.reindex(all_ports, fill_value=0).sort_index()

    score = jensenshannon_wrapper(real_aligned.values, gen_aligned.values, base=2)

    return build_distribution(
        score,
        [str(x) for x in all_ports],
        real_aligned.values,
        gen_aligned.values
    )

def flow_srcport_stateless_connection2dstport_topnkey(real_df_1, gen_df_2, n=10):
    """
    Computes the 1-hit rate between the top-N source ports (by number of
    distinct destination ports) in the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, COUNT(DISTINCT dstport) AS n
        FROM <table_name>
        GROUP BY srcport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per source port with
        the distinct destination port count in the 'n' column and is
        already sorted in descending order of distinct destination port count.

    Returns:
        float: 1 - hit rate between real and generated top-N source ports.
    """

    # SQL already returns rows ordered by n DESC
    real_top_ports = set(real_df_1.head(n)["srcport"])
    gen_top_ports = set(gen_df_2.head(n)["srcport"])

    hits = len(real_top_ports.intersection(gen_top_ports))

    score = 1 - hits / n

    return build_topnkey(
        score,
        real_top_ports,
        gen_top_ports
    )

def flow_srcport_stateless_connection2dstport_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct destination ports associated with the top N source ports.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, COUNT(DISTINCT dstport) AS n
        FROM <table_name>
        GROUP BY srcport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per source port with
        the distinct destination port count in the 'n' column.
    """

    # Extract top-N distinct destination port counts from SQL aggregation results
    real_conn = real_df_1.head(n)["n"].to_numpy()
    gen_conn = gen_df_2.head(n)["n"].to_numpy()

    # Pad arrays to equal length
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

def flow_srcport_stateless_connection2dstport_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distribution
    of distinct destination port counts per source port in the real and
    generated datasets. The comparison is port-specific (not agnostic).

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, COUNT(DISTINCT dstport) AS n
        FROM <table_name>
        GROUP BY srcport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per source port with
        the distinct destination port count stored in the 'n' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) value in [0, 1].
    """

    # Normalize distinct destination port counts returned by SQL
    real_dist = (real_df_1.set_index("srcport")["n"] / real_df_1["n"].sum())

    gen_dist = (gen_df_2.set_index("srcport")["n"] / gen_df_2["n"].sum())

    # Align distributions by source port
    all_ports = set(real_dist.index).union(set(gen_dist.index))

    real_aligned = real_dist.reindex(all_ports, fill_value=0).sort_index()
    gen_aligned = gen_dist.reindex(all_ports, fill_value=0).sort_index()

    score = jensenshannon_wrapper(real_aligned.values, gen_aligned.values, base=2)

    return build_distribution(
        score,
        [str(x) for x in all_ports],
        real_aligned.values,
        gen_aligned.values
    )

def flow_srcport_stateless_connection2dstipport_topnkey(real_df_1, gen_df_2, n=10):
    """
    Computes the 1-hit rate between the top-N source ports (by number of
    distinct (dstip, dstport) pairs) in the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, COUNT(DISTINCT (dstip, dstport)) AS n
        FROM <table_name>
        GROUP BY srcport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per source port with
        the distinct (dstip, dstport) pair count stored in the 'n' column
        and is already sorted in descending order of pair count.

    Returns:
        float: 1 - hit rate between real and generated top-N source ports.
    """

    real_top_ports = set(real_df_1.head(n)["srcport"])
    gen_top_ports = set(gen_df_2.head(n)["srcport"])

    hits = len(real_top_ports.intersection(gen_top_ports))

    score = 1 - hits / n

    return build_topnkey(
        score,
        real_top_ports,
        gen_top_ports
    )

def flow_srcport_stateless_connection2dstipport_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct (dstip, dstport) pairs associated with the top N source ports.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, COUNT(DISTINCT (dstip, dstport)) AS n
        FROM <table_name>
        GROUP BY srcport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per source port with
        the distinct (dstip, dstport) pair count in the 'n' column.
    """

    # Extract top-N distinct (dstip, dstport) pair counts from SQL aggregation results
    real_top = real_df_1.head(n)["n"].to_numpy()
    gen_top = gen_df_2.head(n)["n"].to_numpy()

    # Pad arrays to equal length
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

def flow_srcport_stateless_connection2dstipport_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distribution
    of distinct (dstip, dstport) pair counts per source port in the real
    and generated datasets. The comparison is port-specific (not agnostic).

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport, COUNT(DISTINCT (dstip, dstport)) AS n
        FROM <table_name>
        GROUP BY srcport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per source port with
        the distinct (dstip, dstport) pair count stored in the 'n' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) value in [0, 1].
    """

    real_dist = (real_df_1.set_index("srcport")["n"] / real_df_1["n"].sum())

    gen_dist = (gen_df_2.set_index("srcport")["n"] / gen_df_2["n"].sum())

    all_ports = set(real_dist.index).union(set(gen_dist.index))

    real_aligned = real_dist.reindex(all_ports, fill_value=0).sort_index()
    gen_aligned = gen_dist.reindex(all_ports, fill_value=0).sort_index()

    score = jensenshannon_wrapper(real_aligned.values, gen_aligned.values, base=2)

    return build_distribution(
        score,
        [str(x) for x in all_ports],
        real_aligned.values,
        gen_aligned.values
    )

def flow_srcport_stateless_connection2flow_topnkey(real_df_1, gen_df_2, n=10):
    """
    Computes the 1-hit rate between the top-N source ports (by number of
    distinct flows) in the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport,
               COUNT(
                   DISTINCT (srcip, dstip, srcport, dstport, proto)
               ) AS n
        FROM <table_name>
        GROUP BY srcport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per source port with
        the distinct flow count in the 'n' column and is already sorted
        in descending order of flow count.

    Returns:
        float: 1 - hit rate between the top-N source ports by flow count.
    """

    real_top_ports = set(real_df_1.head(n)["srcport"])
    gen_top_ports = set(gen_df_2.head(n)["srcport"])

    hits = len(real_top_ports.intersection(gen_top_ports))

    score = 1 - hits / n

    return build_topnkey(
        score,
        real_top_ports,
        gen_top_ports
    )

def flow_srcport_stateless_connection2flow_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct flows (5-tuples) associated with the top N source ports.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport,
               COUNT(
                   DISTINCT (srcip, dstip, srcport, dstport, proto)
               ) AS n
        FROM <table_name>
        GROUP BY srcport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per source port with
        the distinct flow count in the 'n' column.
    """

    # Extract top-N distinct flow counts from SQL aggregation results
    real_top = real_df_1.head(n)["n"].to_numpy()
    gen_top = gen_df_2.head(n)["n"].to_numpy()

    # Pad to equal length
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

def flow_srcport_stateless_connection2flow_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distribution
    of distinct flow counts per source port in the real and generated
    datasets. The comparison is port-specific (not agnostic).

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT srcport,
               COUNT(
                   DISTINCT (srcip, dstip, srcport, dstport, proto)
               ) AS n
        FROM <table_name>
        GROUP BY srcport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per source port with
        the distinct flow count stored in the 'n' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) value in [0, 1].
    """

    real_dist = (real_df_1.set_index("srcport")["n"] / real_df_1["n"].sum())

    gen_dist = (gen_df_2.set_index("srcport")["n"] / gen_df_2["n"].sum())

    all_ports = set(real_dist.index).union(set(gen_dist.index))

    real_aligned = real_dist.reindex(all_ports, fill_value=0).sort_index()
    gen_aligned = gen_dist.reindex(all_ports, fill_value=0).sort_index()

    score = jensenshannon_wrapper(real_aligned.values, gen_aligned.values, base=2)

    return build_distribution(
        score,
        [str(x) for x in all_ports],
        real_aligned.values,
        gen_aligned.values
    )


# Per Destination Port Aggregations
def flow_dstport_stateless_packet_topnkey(real_df_1, gen_df_2, n=10):
    """
    Computes the 1-hit rate between the top-N destination ports (by packet count)
    in the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport, COUNT(*) AS pkts
        FROM <table_name>
        GROUP BY dstport
        ORDER BY pkts DESC

        Therefore, each DataFrame contains one row per destination port with
        the aggregated packet count in the 'pkts' column and is already
        sorted in descending order of packet count.

    Returns:
        float: 1 - hit rate between real and generated top-N destination ports.
    """

    real_top_ports = set(real_df_1.head(n)["dstport"])
    gen_top_ports = set(gen_df_2.head(n)["dstport"])

    hits = len(real_top_ports.intersection(gen_top_ports))

    score = 1 - hits / n

    return build_topnkey(
        score,
        real_top_ports,
        gen_top_ports
    )

def flow_dstport_stateless_packet_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the packet counts
    for the top N destination ports.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport, COUNT(*) AS pkts
        FROM <table_name>
        GROUP BY dstport
        ORDER BY pkts DESC

        Therefore, each DataFrame contains one row per destination port with
        the aggregated packet count in the 'pkts' column.
    """

    # Extract top-N packet counts from SQL aggregation results
    real_counts = real_df_1.head(n)["pkts"].to_numpy()
    gen_counts = gen_df_2.head(n)["pkts"].to_numpy()

    # Pad to equal length
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

def flow_dstport_stateless_bytes_topnkey(real_df_1, gen_df_2, n=10):
    """
    Computes 1 - hit rate between the top-N destination ports by total bytes.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport,
               SUM(pkt_len) AS bytes
        FROM <table_name>
        GROUP BY dstport
        ORDER BY bytes DESC

        Therefore, each DataFrame contains one row per destination port
        with the aggregated byte count in the 'bytes' column.
    """

    real_top_ports = set(real_df_1.head(n)["dstport"])
    gen_top_ports = set(gen_df_2.head(n)["dstport"])

    hits = len(real_top_ports.intersection(gen_top_ports))

    score = 1 - hits / n

    return build_topnkey(
        score,
        real_top_ports,
        gen_top_ports
    )

def flow_dstport_stateless_bytes_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the total bytes
    associated with the top N destination ports.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport, SUM(pkt_len) AS bytes
        FROM <table_name>
        GROUP BY dstport
        ORDER BY bytes DESC

        Therefore, each DataFrame contains one row per destination port with
        the aggregated byte count in the 'bytes' column.
    """

    import numpy as np

    # Extract top-N byte counts from SQL aggregation results
    real_bytes = real_df_1.head(n)["bytes"].to_numpy()
    gen_bytes = gen_df_2.head(n)["bytes"].to_numpy()

    # Pad arrays to equal length
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

def flow_dstport_stateless_bytes_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distribution
    of total bytes per destination port.

    Inputs are SQL aggregation results:

        SELECT dstport,
               SUM(pkt_len) AS bytes
        FROM <table_name>
        GROUP BY dstport
        ORDER BY bytes DESC
    """

    real_bytes = real_df_1.set_index("dstport")["bytes"]
    gen_bytes = gen_df_2.set_index("dstport")["bytes"]

    all_ports = real_bytes.index.union(gen_bytes.index)

    real_aligned = real_bytes.reindex(all_ports, fill_value=0)
    gen_aligned = gen_bytes.reindex(all_ports, fill_value=0)

    score = jensenshannon_wrapper(real_aligned.to_numpy(), gen_aligned.to_numpy())

    return build_distribution(
        score,
        [str(x) for x in all_ports],
        real_aligned.values,
        gen_aligned.values
    )

def flow_dstport_stateless_connection2dstip_topnkey(real_df_1, gen_df_2, n=10):
    """
    Computes the 1-hit rate between the top-N destination ports (by number of
    distinct destination IPs) in the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport, COUNT(DISTINCT dstip) AS n
        FROM <table_name>
        GROUP BY dstport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per destination port
        with the distinct destination IP count in the 'n' column.
    """

    # SQL already returns rows ordered by n DESC
    real_top_ports = set(real_df_1.head(n)["dstport"])
    gen_top_ports = set(gen_df_2.head(n)["dstport"])

    hits = len(real_top_ports.intersection(gen_top_ports))

    score = 1 - hits / n

    return build_topnkey(
        score,
        real_top_ports,
        gen_top_ports
    )

def flow_dstport_stateless_connection2dstip_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct destination IPs associated with the top N destination ports.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport, COUNT(DISTINCT dstip) AS n
        FROM <table_name>
        GROUP BY dstport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per destination port
        with the distinct destination IP count in the 'n' column.
    """

    # Extract top-N distinct destination IP counts from SQL aggregation results
    real_top = real_df_1.head(n)["n"].to_numpy()
    gen_top = gen_df_2.head(n)["n"].to_numpy()

    # Pad with zeros to equal length
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

def flow_dstport_stateless_connection2dstip_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distribution of
    distinct destination IP counts across destination ports.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport, COUNT(DISTINCT dstip) AS n
        FROM <table_name>
        GROUP BY dstport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per destination port
        with the distinct destination IP count in the 'n' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) value in [0, 1].
    """

    real_dist = (real_df_1.set_index("dstport")["n"] / real_df_1["n"].sum())

    gen_dist = (gen_df_2.set_index("dstport")["n"] / gen_df_2["n"].sum())

    all_ports = set(real_dist.index).union(set(gen_dist.index))

    real_aligned = real_dist.reindex(all_ports, fill_value=0).sort_index()
    gen_aligned = gen_dist.reindex(all_ports, fill_value=0).sort_index()

    score = jensenshannon_wrapper(real_aligned.values, gen_aligned.values, base=2)

    return build_distribution(
        score,
        [str(x) for x in all_ports],
        real_aligned.values,
        gen_aligned.values
    )

def flow_dstport_stateless_connection2srcip_topnkey(real_df_1, gen_df_2, n=10):
    """
    Computes the 1-hit rate between the top-N destination ports (by number of
    distinct source IPs) in the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport, COUNT(DISTINCT srcip) AS n
        FROM <table_name>
        GROUP BY dstport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per destination port with
        the distinct source IP count in the 'n' column and is already sorted
        in descending order of distinct source IP count.

    Returns:
        float: 1 - hit rate between real and generated top-N destination ports.
    """

    real_top_ports = set(real_df_1.head(n)["dstport"])
    gen_top_ports = set(gen_df_2.head(n)["dstport"])

    hits = len(real_top_ports.intersection(gen_top_ports))

    score = 1 - hits / n

    return build_topnkey(
        score,
        real_top_ports,
        gen_top_ports
    )

def flow_dstport_stateless_connection2srcip_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct source IPs associated with the top N destination ports.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport, COUNT(DISTINCT srcip) AS n
        FROM <table_name>
        GROUP BY dstport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per destination port
        with the distinct source IP count in the 'n' column.
    """

    # Extract top-N distinct source IP counts from SQL aggregation results
    real_top = real_df_1.head(n)["n"].to_numpy()
    gen_top = gen_df_2.head(n)["n"].to_numpy()

    # Pad with zeros to equal length
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

def flow_dstport_stateless_connection2srcip_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distribution of
    distinct source IP counts across destination ports.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport, COUNT(DISTINCT srcip) AS n
        FROM <table_name>
        GROUP BY dstport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per destination port with
        the distinct source IP count in the 'n' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) value in [0, 1].
    """

    real_dist = (real_df_1.set_index("dstport")["n"] / real_df_1["n"].sum())

    gen_dist = (gen_df_2.set_index("dstport")["n"] / gen_df_2["n"].sum())

    all_ports = set(real_dist.index).union(set(gen_dist.index))

    real_aligned = real_dist.reindex(all_ports, fill_value=0).sort_index()
    gen_aligned = gen_dist.reindex(all_ports, fill_value=0).sort_index()

    score = jensenshannon_wrapper(real_aligned.values, gen_aligned.values, base=2)

    return build_distribution(
        score,
        [str(x) for x in all_ports],
        real_aligned.values,
        gen_aligned.values
    )

def flow_dstport_stateless_connection2srcport_topnkey(real_df_1, gen_df_2, n=10):
    """
    Computes the 1-hit rate between the top-N destination ports (by number of
    distinct source ports) in the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport, COUNT(DISTINCT srcport) AS n
        FROM <table_name>
        GROUP BY dstport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per destination port
        with the distinct source port count in the 'n' column and is
        already sorted in descending order of distinct source port count.

    Returns:
        float: 1 - hit rate between real and generated top-N destination ports.
    """

    real_top_ports = set(real_df_1.head(n)["dstport"])
    gen_top_ports = set(gen_df_2.head(n)["dstport"])

    hits = len(real_top_ports.intersection(gen_top_ports))

    score = 1 - hits / n

    return build_topnkey(
        score,
        real_top_ports,
        gen_top_ports
    )

def flow_dstport_stateless_connection2srcport_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct source ports associated with the top N destination ports.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport, COUNT(DISTINCT srcport) AS n
        FROM <table_name>
        GROUP BY dstport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per destination port
        with the distinct source port count in the 'n' column.
    """

    # Extract top-N distinct source port counts from SQL aggregation results
    real_top = real_df_1.head(n)["n"].to_numpy()
    gen_top = gen_df_2.head(n)["n"].to_numpy()

    # Pad with zeros to equal length
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

def flow_dstport_stateless_connection2srcport_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distribution of
    distinct source port counts across destination ports.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport, COUNT(DISTINCT srcport) AS n
        FROM <table_name>
        GROUP BY dstport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per destination port
        with the distinct source port count in the 'n' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) value in [0, 1].
    """

    real_dist = (real_df_1.set_index("dstport")["n"] / real_df_1["n"].sum())

    gen_dist = (gen_df_2.set_index("dstport")["n"] / gen_df_2["n"].sum())

    all_ports = set(real_dist.index).union(set(gen_dist.index))

    real_aligned = real_dist.reindex(all_ports, fill_value=0).sort_index()
    gen_aligned = gen_dist.reindex(all_ports, fill_value=0).sort_index()

    score = jensenshannon_wrapper(real_aligned.values, gen_aligned.values, base=2)

    return build_distribution(
        score,
        [str(x) for x in all_ports],
        real_aligned.values,
        gen_aligned.values
    )

def flow_dstport_stateless_connection2srcipport_topnkey(real_df_1, gen_df_2, n=10):
    """
    Computes the 1-hit rate between the top-N destination ports (by number of
    distinct (srcip, srcport) pairs) in the real and generated datasets.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport, COUNT(DISTINCT (srcip, srcport)) AS n
        FROM <table_name>
        GROUP BY dstport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per destination port
        with the distinct (srcip, srcport) pair count in the 'n' column
        and is already sorted in descending order of pair count.

    Returns:
        float: 1 - hit rate between real and generated top-N destination ports.
    """

    real_top_ports = set(real_df_1.head(n)["dstport"])
    gen_top_ports = set(gen_df_2.head(n)["dstport"])

    hits = len(real_top_ports.intersection(gen_top_ports))

    score = 1 - hits / n

    return build_topnkey(
        score,
        real_top_ports,
        gen_top_ports
    )

def flow_dstport_stateless_connection2srcipport_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct (srcip, srcport) pairs associated with the top N destination ports.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport, COUNT(DISTINCT (srcip, srcport)) AS n
        FROM <table_name>
        GROUP BY dstport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per destination port
        with the distinct (srcip, srcport) pair count in the 'n' column.
    """

    # Extract top-N distinct (srcip, srcport) pair counts from SQL aggregation results
    real_top = real_df_1.head(n)["n"].to_numpy()
    gen_top = gen_df_2.head(n)["n"].to_numpy()

    # Pad arrays to equal length
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

def flow_dstport_stateless_connection2srcipport_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distribution of
    distinct (srcip, srcport) pair counts across destination ports.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport, COUNT(DISTINCT (srcip, srcport)) AS n
        FROM <table_name>
        GROUP BY dstport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per destination port
        with the distinct (srcip, srcport) pair count in the 'n' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) value in [0, 1].
    """

    real_dist = (real_df_1.set_index("dstport")["n"] / real_df_1["n"].sum())

    gen_dist = (gen_df_2.set_index("dstport")["n"] / gen_df_2["n"].sum())

    all_ports = set(real_dist.index).union(set(gen_dist.index))

    real_aligned = real_dist.reindex(all_ports, fill_value=0).sort_index()
    gen_aligned = gen_dist.reindex(all_ports, fill_value=0).sort_index()

    score = jensenshannon_wrapper(real_aligned.values, gen_aligned.values, base=2)

    return build_distribution(
        score,
        [str(x) for x in all_ports],
        real_aligned.values,
        gen_aligned.values
    )

def flow_dstport_stateless_connection2flow_topnkey(real_df_1, gen_df_2, n=10):
    """
    Computes the 1 - hit rate between the top-N destination ports by
    distinct flow count.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport,
               COUNT(
                   DISTINCT (srcip, dstip, srcport, dstport, proto)
               ) AS n
        FROM <table_name>
        GROUP BY dstport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per destination port
        with the distinct flow count in the 'n' column.
    """

    # Extract top-N destination ports from SQL aggregation results
    real_top = set(real_df_1.head(n)["dstport"])
    gen_top = set(gen_df_2.head(n)["dstport"])

    # Compute 1 - hit rate
    hits = len(real_top.intersection(gen_top))

    score = 1 - hits / n

    return build_topnkey(
        score,
        real_top,
        gen_top
    )

def flow_dstport_stateless_connection2flow_topnvalue(real_df_1, gen_df_2, n=10):
    """
    Computes the average Absolute Relative Error (ARE) of the number of
    distinct flows (5-tuples) associated with the top N destination ports.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport,
               COUNT(
                   DISTINCT (srcip, dstip, srcport, dstport, proto)
               ) AS n
        FROM <table_name>
        GROUP BY dstport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per destination port
        with the distinct flow count in the 'n' column.
    """

    # Extract top-N distinct flow counts from SQL aggregation results
    real_top = real_df_1.head(n)["n"].to_numpy()
    gen_top = gen_df_2.head(n)["n"].to_numpy()

    # Pad to equal length
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

def flow_dstport_stateless_connection2flow_distribution(real_df_1, gen_df_2, n=10):
    """
    Computes the Jensen-Shannon Divergence (JSD) between the distribution of
    distinct flow counts across destination ports.

    Note:
        The inputs are SQL aggregation results generated from:

        SELECT dstport,
               COUNT(
                   DISTINCT (srcip, dstip, srcport, dstport, proto)
               ) AS n
        FROM <table_name>
        GROUP BY dstport
        ORDER BY n DESC

        Therefore, each DataFrame contains one row per destination port
        with the distinct flow count stored in the 'n' column.

    Returns:
        float: Jensen-Shannon Divergence (JSD) value in [0, 1].
    """

    real_dist = (real_df_1.set_index("dstport")["n"] / real_df_1["n"].sum())

    gen_dist = (gen_df_2.set_index("dstport")["n"] / gen_df_2["n"].sum())

    all_ports = set(real_dist.index).union(set(gen_dist.index))

    real_aligned = real_dist.reindex(all_ports, fill_value=0).sort_index()
    gen_aligned = gen_dist.reindex(all_ports, fill_value=0).sort_index()

    score = jensenshannon_wrapper(real_aligned.values, gen_aligned.values, base=2)

    return build_distribution(
        score,
        [str(x) for x in all_ports],
        real_aligned.values,
        gen_aligned.values
    )
