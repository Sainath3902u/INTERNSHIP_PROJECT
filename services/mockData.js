export const mockData = {
  overall_score: 0.18,
  packet_level: {
    score: 0.12,
    name: "Packet Level Metrics",
    queries: [
      {
        id: "packet-size-dist",
        name: "Packet Size Distribution",
        abbreviation: "PSD",
        distance_score: 0.08,
        sql: "SELECT packet_size, COUNT(*) FROM real_data GROUP BY packet_size ORDER BY packet_size ASC;",
        description:
        "Measures the frequency distribution of network packets across different packet sizes. It helps identify the typical packet sizes observed in network traffic.",
        chartData: [
          { name: "64B", real: 1200, synthetic: 1150 },
          { name: "128B", real: 850, synthetic: 900 },
          { name: "512B", real: 400, synthetic: 410 },
          { name: "1500B", real: 3200, synthetic: 2950 }
        ]
      },
      {
        id: "protocol-co-occurrence",
        name: "Protocol Co-occurrence Rate",
        abbreviation: "PCR",
        distance_score: 0.15,
        sql: "SELECT protocol, COUNT(*) FROM real_data GROUP BY protocol;",
        description:
        "Shows how often different network protocols are observed together in the dataset. It helps verify whether the synthetic traffic preserves the protocol composition of the original data.",
        chartData: [
          { name: "TCP", real: 75, synthetic: 70 },
          { name: "UDP", real: 20, synthetic: 22 },
          { name: "ICMP", real: 5, synthetic: 8 }
        ]
      }
    ]
  },
  flow_stateless: {
    score: 0.21,
    name: "Flow Stateless Metrics",
    queries: [
      {
        id: "src-ip-entropy",
        name: "Source IP Entropy Profile",
        abbreviation: "SIEP",
        distance_score: 0.21,
        sql: "SELECT src_ip, COUNT(*) as flow_count FROM real_flows GROUP BY src_ip;",
        description:
        "Summarizes the distribution of source IP addresses across flows, showing how concentrated or diverse sources are in the network traffic.",
        chartData: [
          { name: "High Density", real: 450, synthetic: 310 },
          { name: "Medium Density", real: 300, synthetic: 340 },
          { name: "Low Density", real: 150, synthetic: 200 }
        ]
      }
    ]
  },
  flow_stateful: {
    score: 0.34,
    name: "Flow Stateful Metrics",
    queries: [
      {
        id: "connection-duration",
        name: "Connection Duration Analysis",
        abbreviation: "CDA",
        distance_score: 0.34,
        sql: "SELECT duration_bins, COUNT(*) FROM stateful_summary GROUP BY duration_bins;",
        description:
        "Analyzes how connection durations are distributed across short, medium, and long-lived sessions to validate whether synthetic traffic timing matches real traffic.",
        chartData: [
          { name: "<1s", real: 5000, synthetic: 3800 },
          { name: "1s-10s", real: 2500, synthetic: 2900 },
          { name: "10s-1m", real: 800, synthetic: 1200 },
          { name: ">1m", real: 200, synthetic: 150 }
        ]
      }
    ]
  }
};