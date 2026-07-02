# Synthetic Packet Trace Evaluation Queries

Exhaustive list of every evaluation query in `metrics.py`, organized into the
three categories defined by `eval_metrics`: **packet level**, **flow level
stateless**, **flow level stateful**. Each query has an abbreviation, a natural
language description, and SQL.

There are **70 queries**: 29 packet level, 21 flow stateless, 20 flow stateful.

## Notes

- Each query is run on the **real** trace and the **synthetic** trace; the two
  result sets are compared with a distance metric to score fidelity. This
  document lists only the **queries**, not the distance metrics.
- In code most queries appear as 2–3 functions suffixed `_topnvalue`,
  `_topnkey`, `_distribution`. Those are the *same query* compared with different
  distance metrics (top-N values, top-N key overlap, full distribution), so each
  is listed once here.
- Schema: `packets(srcip, dstip, srcport, dstport, proto, time, pkt_len)`.
- `COUNT(DISTINCT a, b)` = count of distinct tuples `(a, b)` (dialect-dependent).
- `flow` / 5-tuple = `(srcip, dstip, srcport, dstport, proto)`.
- `STDDEV_POP` = population std (code uses `numpy.std`, ddof=0).

---

## 1. Packet Level

### 1a. Global packet statistics

**1. `P-COUNT`** — Total number of packets.
```sql
SELECT COUNT(*) AS total_packets FROM packets;
```

**2. `P-SRCIP-CD`** — Number of distinct source IPs.
```sql
SELECT COUNT(DISTINCT srcip) AS n_src_ips FROM packets;
```

**3. `P-SRCIP-DIST`** — Number of packets sent by each source IP (compared IP-agnostic: values sorted).
```sql
SELECT srcip, COUNT(*) AS pkts FROM packets GROUP BY srcip ORDER BY pkts DESC;
```

**4. `P-DSTIP-CD`** — Number of distinct destination IPs.
```sql
SELECT COUNT(DISTINCT dstip) AS n_dst_ips FROM packets;
```

**5. `P-DSTIP-DIST`** — Number of packets received by each destination IP (IP-agnostic).
```sql
SELECT dstip, COUNT(*) AS pkts FROM packets GROUP BY dstip ORDER BY pkts DESC;
```

**6. `P-SRCPORT-CD`** — Number of distinct source ports.
```sql
SELECT COUNT(DISTINCT srcport) AS n_src_ports FROM packets;
```

**7. `P-SRCPORT-DIST`** — Number of packets per source port (compared per-port, aligned by port value).
```sql
SELECT srcport, COUNT(*) AS pkts FROM packets GROUP BY srcport;
```

**8. `P-DSTPORT-CD`** — Number of distinct destination ports.
```sql
SELECT COUNT(DISTINCT dstport) AS n_dst_ports FROM packets;
```

**9. `P-DSTPORT-DIST`** — Number of packets per destination port (compared per-port).
```sql
SELECT dstport, COUNT(*) AS pkts FROM packets GROUP BY dstport;
```

**10. `P-PROTO-CD`** — Number of distinct protocols.
```sql
SELECT COUNT(DISTINCT proto) AS n_protocols FROM packets;
```

**11. `P-PROTO-DIST`** — Number of packets per protocol (compared per-protocol).
```sql
SELECT proto, COUNT(*) AS pkts FROM packets GROUP BY proto;
```

**12. `P-TIME-DIST`** — Packet timestamps (normalized to [0,1] across both traces on the distance side).
```sql
SELECT time FROM packets;
```

**13. `P-LEN-SUM`** — Total bytes (sum of packet lengths).
```sql
SELECT SUM(pkt_len) AS total_bytes FROM packets;
```

**14. `P-LEN-AVG`** — Average packet length.
```sql
SELECT AVG(pkt_len) AS avg_pkt_len FROM packets;
```

**15. `P-LEN-DIST`** — Packet lengths (histogrammed by integer length on the distance side).
```sql
SELECT pkt_len FROM packets;
```

### 1b. Per source-port aggregations

**16. `SP-PKT`** — Number of packets per source port.
```sql
SELECT srcport, COUNT(*) AS pkts FROM packets GROUP BY srcport ORDER BY pkts DESC;
```

**17. `SP-BYTE`** — Total bytes per source port.
```sql
SELECT srcport, SUM(pkt_len) AS bytes FROM packets GROUP BY srcport ORDER BY bytes DESC;
```

**18. `SP-CD-SRCIP`** — Distinct source IPs per source port.
```sql
SELECT srcport, COUNT(DISTINCT srcip) AS n FROM packets GROUP BY srcport ORDER BY n DESC;
```

**19. `SP-CD-DSTIP`** — Distinct destination IPs per source port.
```sql
SELECT srcport, COUNT(DISTINCT dstip) AS n FROM packets GROUP BY srcport ORDER BY n DESC;
```

**20. `SP-CD-DSTPORT`** — Distinct destination ports per source port.
```sql
SELECT srcport, COUNT(DISTINCT dstport) AS n FROM packets GROUP BY srcport ORDER BY n DESC;
```

**21. `SP-CD-DSTIPPORT`** — Distinct `(dstip, dstport)` pairs per source port.
```sql
SELECT srcport, COUNT(DISTINCT dstip, dstport) AS n FROM packets GROUP BY srcport ORDER BY n DESC;
```

**22. `SP-CD-FLOW`** — Distinct flows (5-tuples) per source port.
```sql
SELECT srcport, COUNT(DISTINCT srcip, dstip, srcport, dstport, proto) AS n
FROM packets GROUP BY srcport ORDER BY n DESC;
```

### 1c. Per destination-port aggregations

**23. `DP-PKT`** — Number of packets per destination port.
```sql
SELECT dstport, COUNT(*) AS pkts FROM packets GROUP BY dstport ORDER BY pkts DESC;
```

**24. `DP-BYTE`** — Total bytes per destination port.
```sql
SELECT dstport, SUM(pkt_len) AS bytes FROM packets GROUP BY dstport ORDER BY bytes DESC;
```

**25. `DP-CD-DSTIP`** — Distinct destination IPs per destination port.
```sql
SELECT dstport, COUNT(DISTINCT dstip) AS n FROM packets GROUP BY dstport ORDER BY n DESC;
```

**26. `DP-CD-SRCIP`** — Distinct source IPs per destination port.
```sql
SELECT dstport, COUNT(DISTINCT srcip) AS n FROM packets GROUP BY dstport ORDER BY n DESC;
```

**27. `DP-CD-SRCPORT`** — Distinct source ports per destination port.
```sql
SELECT dstport, COUNT(DISTINCT srcport) AS n FROM packets GROUP BY dstport ORDER BY n DESC;
```

**28. `DP-CD-SRCIPPORT`** — Distinct `(srcip, srcport)` pairs per destination port.
```sql
SELECT dstport, COUNT(DISTINCT srcip, srcport) AS n FROM packets GROUP BY dstport ORDER BY n DESC;
```

**29. `DP-CD-FLOW`** — Distinct flows (5-tuples) per destination port.
```sql
SELECT dstport, COUNT(DISTINCT srcip, dstip, srcport, dstport, proto) AS n
FROM packets GROUP BY dstport ORDER BY n DESC;
```

---

## 2. Flow Level Stateless

### 2a. Per source IP

**30. `SI-PKT`** — Number of packets per source IP.
```sql
SELECT srcip, COUNT(*) AS pkts FROM packets GROUP BY srcip ORDER BY pkts DESC;
```

**31. `SI-BYTE`** — Total bytes per source IP.
```sql
SELECT srcip, SUM(pkt_len) AS bytes FROM packets GROUP BY srcip ORDER BY bytes DESC;
```

**32. `SI-CD-SRCPORT`** — Distinct source ports per source IP.
```sql
SELECT srcip, COUNT(DISTINCT srcport) AS n FROM packets GROUP BY srcip ORDER BY n DESC;
```

**33. `SI-CD-DSTIP`** — Distinct destination IPs contacted per source IP.
```sql
SELECT srcip, COUNT(DISTINCT dstip) AS n FROM packets GROUP BY srcip ORDER BY n DESC;
```

**34. `SI-CD-DSTPORT`** — Distinct destination ports contacted per source IP.
```sql
SELECT srcip, COUNT(DISTINCT dstport) AS n FROM packets GROUP BY srcip ORDER BY n DESC;
```

**35. `SI-CD-DSTIPPORT`** — Distinct `(dstip, dstport)` pairs contacted per source IP.
```sql
SELECT srcip, COUNT(DISTINCT dstip, dstport) AS n FROM packets GROUP BY srcip ORDER BY n DESC;
```

**36. `SI-CD-FLOW`** — Distinct flows (5-tuples) per source IP.
```sql
SELECT srcip, COUNT(DISTINCT srcip, dstip, srcport, dstport, proto) AS n
FROM packets GROUP BY srcip ORDER BY n DESC;
```

### 2b. Per destination IP

**37. `DI-PKT`** — Number of packets per destination IP.
```sql
SELECT dstip, COUNT(*) AS pkts FROM packets GROUP BY dstip ORDER BY pkts DESC;
```

**38. `DI-BYTE`** — Total bytes per destination IP.
```sql
SELECT dstip, SUM(pkt_len) AS bytes FROM packets GROUP BY dstip ORDER BY bytes DESC;
```

**39. `DI-CD-DSTPORT`** — Distinct destination ports per destination IP.
```sql
SELECT dstip, COUNT(DISTINCT dstport) AS n FROM packets GROUP BY dstip ORDER BY n DESC;
```

**40. `DI-CD-SRCIP`** — Distinct source IPs contacting per destination IP.
```sql
SELECT dstip, COUNT(DISTINCT srcip) AS n FROM packets GROUP BY dstip ORDER BY n DESC;
```

**41. `DI-CD-SRCPORT`** — Distinct source ports per destination IP.
```sql
SELECT dstip, COUNT(DISTINCT srcport) AS n FROM packets GROUP BY dstip ORDER BY n DESC;
```

**42. `DI-CD-SRCIPPORT`** — Distinct `(srcip, srcport)` pairs per destination IP.
```sql
SELECT dstip, COUNT(DISTINCT srcip, srcport) AS n FROM packets GROUP BY dstip ORDER BY n DESC;
```

**43. `DI-CD-FLOW`** — Distinct flows (5-tuples) per destination IP.
```sql
SELECT dstip, COUNT(DISTINCT srcip, dstip, srcport, dstport, proto) AS n
FROM packets GROUP BY dstip ORDER BY n DESC;
```

### 2c. Per IP pair `(srcip, dstip)`

**44. `PR-PKT`** — Number of packets per source–destination IP pair.
```sql
SELECT srcip, dstip, COUNT(*) AS pkts FROM packets GROUP BY srcip, dstip ORDER BY pkts DESC;
```

**45. `PR-BYTE`** — Total bytes per IP pair.
```sql
SELECT srcip, dstip, SUM(pkt_len) AS bytes FROM packets GROUP BY srcip, dstip ORDER BY bytes DESC;
```

**46. `PR-CD-SRCPORT`** — Distinct source ports per IP pair.
```sql
SELECT srcip, dstip, COUNT(DISTINCT srcport) AS n FROM packets GROUP BY srcip, dstip ORDER BY n DESC;
```

**47. `PR-CD-DSTPORT`** — Distinct destination ports per IP pair.
```sql
SELECT srcip, dstip, COUNT(DISTINCT dstport) AS n FROM packets GROUP BY srcip, dstip ORDER BY n DESC;
```

**48. `PR-CD-FLOW`** — Distinct flows (5-tuples) per IP pair.
```sql
SELECT srcip, dstip, COUNT(DISTINCT srcip, dstip, srcport, dstport, proto) AS n
FROM packets GROUP BY srcip, dstip ORDER BY n DESC;
```

### 2d. Per 5-tuple flow `(srcip, dstip, srcport, dstport, proto)`

**49. `FT-PKT`** — Number of packets per 5-tuple flow.
```sql
SELECT srcip, dstip, srcport, dstport, proto, COUNT(*) AS pkts
FROM packets GROUP BY srcip, dstip, srcport, dstport, proto ORDER BY pkts DESC;
```

**50. `FT-BYTE`** — Total bytes per 5-tuple flow.
```sql
SELECT srcip, dstip, srcport, dstport, proto, SUM(pkt_len) AS bytes
FROM packets GROUP BY srcip, dstip, srcport, dstport, proto ORDER BY bytes DESC;
```

---

## 3. Flow Level Stateful

Timing/rate metrics that depend on packet ordering within each entity.
`gap` = inter-arrival time between consecutive packets of an entity (ordered by `time`).

### 3a. Per source IP

**51. `SI-AINT`** — Average packet inter-arrival time per source IP (source IPs with > 10 packets).
```sql
WITH gaps AS (
    SELECT srcip, time - LAG(time) OVER (PARTITION BY srcip ORDER BY time) AS gap
    FROM packets
)
SELECT srcip, AVG(gap) AS avg_interval
FROM gaps GROUP BY srcip HAVING COUNT(*) > 10 ORDER BY avg_interval DESC;
```

**52. `SI-DUR`** — Flow duration (last − first packet time) per source IP.
```sql
SELECT srcip, MAX(time) - MIN(time) AS duration
FROM packets GROUP BY srcip ORDER BY duration DESC;
```

**53. `SI-BRATE`** — Byte rate (bytes ÷ duration) per source IP (source IPs with > 1 packet; zero duration → 1).
```sql
SELECT srcip,
       SUM(pkt_len) / CASE WHEN MAX(time) - MIN(time) = 0 THEN 1
                           ELSE MAX(time) - MIN(time) END AS byte_rate
FROM packets GROUP BY srcip HAVING COUNT(*) > 1 ORDER BY byte_rate DESC;
```

**54. `SI-SINT`** — Standard deviation of inter-arrival times per source IP.
```sql
WITH gaps AS (
    SELECT srcip, time - LAG(time) OVER (PARTITION BY srcip ORDER BY time) AS gap
    FROM packets
)
SELECT srcip, STDDEV_POP(gap) AS std_iat
FROM gaps WHERE gap IS NOT NULL GROUP BY srcip;
```

**55. `SI-CINT`** — Coefficient of variation (std ÷ mean) of inter-arrival times per source IP.
```sql
WITH gaps AS (
    SELECT srcip, time - LAG(time) OVER (PARTITION BY srcip ORDER BY time) AS gap
    FROM packets
)
SELECT srcip, STDDEV_POP(gap) / AVG(gap) AS cv_iat
FROM gaps WHERE gap IS NOT NULL GROUP BY srcip HAVING AVG(gap) > 0;
```

### 3b. Per destination IP

**56. `DI-AINT`** — Average packet inter-arrival time per destination IP (destination IPs with > 10 packets).
```sql
WITH gaps AS (
    SELECT dstip, time - LAG(time) OVER (PARTITION BY dstip ORDER BY time) AS gap
    FROM packets
)
SELECT dstip, AVG(gap) AS avg_interval
FROM gaps GROUP BY dstip HAVING COUNT(*) > 10 ORDER BY avg_interval DESC;
```

**57. `DI-DUR`** — Flow duration per destination IP.
```sql
SELECT dstip, MAX(time) - MIN(time) AS duration
FROM packets GROUP BY dstip ORDER BY duration DESC;
```

**58. `DI-BRATE`** — Byte rate per destination IP (destination IPs with > 1 packet; zero duration → 1).
```sql
SELECT dstip,
       SUM(pkt_len) / CASE WHEN MAX(time) - MIN(time) = 0 THEN 1
                           ELSE MAX(time) - MIN(time) END AS byte_rate
FROM packets GROUP BY dstip HAVING COUNT(*) > 1 ORDER BY byte_rate DESC;
```

**59. `DI-SINT`** — Standard deviation of inter-arrival times per destination IP.
```sql
WITH gaps AS (
    SELECT dstip, time - LAG(time) OVER (PARTITION BY dstip ORDER BY time) AS gap
    FROM packets
)
SELECT dstip, STDDEV_POP(gap) AS std_iat
FROM gaps WHERE gap IS NOT NULL GROUP BY dstip;
```

**60. `DI-CINT`** — Coefficient of variation of inter-arrival times per destination IP.
```sql
WITH gaps AS (
    SELECT dstip, time - LAG(time) OVER (PARTITION BY dstip ORDER BY time) AS gap
    FROM packets
)
SELECT dstip, STDDEV_POP(gap) / AVG(gap) AS cv_iat
FROM gaps WHERE gap IS NOT NULL GROUP BY dstip HAVING AVG(gap) > 0;
```

### 3c. Per IP pair `(srcip, dstip)`

**61. `PR-AINT`** — Average packet inter-arrival time per IP pair (pairs with > 10 packets).
```sql
WITH gaps AS (
    SELECT srcip, dstip,
           time - LAG(time) OVER (PARTITION BY srcip, dstip ORDER BY time) AS gap
    FROM packets
)
SELECT srcip, dstip, AVG(gap) AS avg_interval
FROM gaps GROUP BY srcip, dstip HAVING COUNT(*) > 10 ORDER BY avg_interval DESC;
```

**62. `PR-DUR`** — Flow duration per IP pair.
```sql
SELECT srcip, dstip, MAX(time) - MIN(time) AS duration
FROM packets GROUP BY srcip, dstip ORDER BY duration DESC;
```

**63. `PR-BRATE`** — Byte rate per IP pair (pairs with > 1 packet; zero duration → 1).
```sql
SELECT srcip, dstip,
       SUM(pkt_len) / CASE WHEN MAX(time) - MIN(time) = 0 THEN 1
                           ELSE MAX(time) - MIN(time) END AS byte_rate
FROM packets GROUP BY srcip, dstip HAVING COUNT(*) > 1 ORDER BY byte_rate DESC;
```

**64. `PR-SINT`** — Standard deviation of inter-arrival times per IP pair.
```sql
WITH gaps AS (
    SELECT srcip, dstip,
           time - LAG(time) OVER (PARTITION BY srcip, dstip ORDER BY time) AS gap
    FROM packets
)
SELECT srcip, dstip, STDDEV_POP(gap) AS std_iat
FROM gaps WHERE gap IS NOT NULL GROUP BY srcip, dstip;
```

**65. `PR-CINT`** — Coefficient of variation of inter-arrival times per IP pair.
```sql
WITH gaps AS (
    SELECT srcip, dstip,
           time - LAG(time) OVER (PARTITION BY srcip, dstip ORDER BY time) AS gap
    FROM packets
)
SELECT srcip, dstip, STDDEV_POP(gap) / AVG(gap) AS cv_iat
FROM gaps WHERE gap IS NOT NULL GROUP BY srcip, dstip HAVING AVG(gap) > 0;
```

### 3d. Per 5-tuple flow `(srcip, dstip, srcport, dstport, proto)`

**66. `FT-AINT`** — Average packet inter-arrival time per 5-tuple flow (flows with > 10 packets).
```sql
WITH gaps AS (
    SELECT srcip, dstip, srcport, dstport, proto,
           time - LAG(time) OVER (
               PARTITION BY srcip, dstip, srcport, dstport, proto ORDER BY time) AS gap
    FROM packets
)
SELECT srcip, dstip, srcport, dstport, proto, AVG(gap) AS avg_interval
FROM gaps GROUP BY srcip, dstip, srcport, dstport, proto
HAVING COUNT(*) > 10 ORDER BY avg_interval DESC;
```

**67. `FT-DUR`** — Flow duration per 5-tuple flow.
```sql
SELECT srcip, dstip, srcport, dstport, proto, MAX(time) - MIN(time) AS duration
FROM packets GROUP BY srcip, dstip, srcport, dstport, proto ORDER BY duration DESC;
```

**68. `FT-BRATE`** — Byte rate per 5-tuple flow (flows with > 1 packet; zero duration → 1).
```sql
SELECT srcip, dstip, srcport, dstport, proto,
       SUM(pkt_len) / CASE WHEN MAX(time) - MIN(time) = 0 THEN 1
                           ELSE MAX(time) - MIN(time) END AS byte_rate
FROM packets GROUP BY srcip, dstip, srcport, dstport, proto
HAVING COUNT(*) > 1 ORDER BY byte_rate DESC;
```

**69. `FT-SINT`** — Standard deviation of inter-arrival times per 5-tuple flow.
```sql
WITH gaps AS (
    SELECT srcip, dstip, srcport, dstport, proto,
           time - LAG(time) OVER (
               PARTITION BY srcip, dstip, srcport, dstport, proto ORDER BY time) AS gap
    FROM packets
)
SELECT srcip, dstip, srcport, dstport, proto, STDDEV_POP(gap) AS std_iat
FROM gaps WHERE gap IS NOT NULL GROUP BY srcip, dstip, srcport, dstport, proto;
```

**70. `FT-CINT`** — Coefficient of variation of inter-arrival times per 5-tuple flow.
```sql
WITH gaps AS (
    SELECT srcip, dstip, srcport, dstport, proto,
           time - LAG(time) OVER (
               PARTITION BY srcip, dstip, srcport, dstport, proto ORDER BY time) AS gap
    FROM packets
)
SELECT srcip, dstip, srcport, dstport, proto, STDDEV_POP(gap) / AVG(gap) AS cv_iat
FROM gaps WHERE gap IS NOT NULL
GROUP BY srcip, dstip, srcport, dstport, proto HAVING AVG(gap) > 0;
```

---

## Appendix: defined but not registered in `eval_metrics`

These query functions exist in `metrics.py` but are commented out (not run):

- **Packet level**: `flag` count-distinct / distribution, `ttl` average /
  distribution (the `flag` and `ttl` columns are not loaded by
  `read_network_packets`).
- **Flow stateful**: the `srcport` and `dstport` families of average packet
  interval, flow duration, and byte rate (the `srcport` / `dstport` *stateless*
  families above are active, registered under the packet group).
