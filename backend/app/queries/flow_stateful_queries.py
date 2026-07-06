FLOW_STATEFUL = [
  
  # Per Source IP
  
  {
      "id": "SI-AINT",
      "section": "Flow Level Stateful",
      "sub_section": "Per Source IP",
      "description": "Average packet inter-arrival time per source IP (source IPs with more than 10 packets)",
      "category": "flow_level_stateful",

      "metric": [
        "flow_srcip_stateful_avgpacketinterval_topnvalue",
        "flow_srcip_stateful_avgpacketinterval_distribution"
      ],

      "sql": """
        SELECT
            srcip,
            AVG(gap) AS avg_interval
        FROM {table_name}_srcip_gaps
        GROUP BY srcip
        HAVING COUNT(*) > 10
        ORDER BY avg_interval DESC
      """
  },
  # {
  #     "id": "SI-DUR",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per Source IP",
  #     "description": "Flow duration per source IP",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_srcip_stateful_flowduration_topnvalue",
  #       "flow_srcip_stateful_flowduration_distribution"
  #     ],

  #     "sql": """
  #     SELECT srcip, MAX(time) - MIN(time) AS duration
  #     FROM {table_name}
  #     GROUP BY srcip
  #     ORDER BY duration DESC
  #     """
  # },
  # {
  #     "id": "SI-BRATE",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per Source IP",
  #     "description": "Byte rate per source IP",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_srcip_stateful_byterate_topnvalue",
  #       "flow_srcip_stateful_byterate_distribution"
  #     ],

  #     "sql": """
  #     SELECT srcip,
  #           SUM(pkt_len) /
  #           CASE
  #               WHEN MAX(time) - MIN(time) = 0 THEN 1
  #               ELSE MAX(time) - MIN(time)
  #           END AS byte_rate
  #     FROM {table_name}
  #     GROUP BY srcip
  #     HAVING COUNT(*) > 1
  #     ORDER BY byte_rate DESC
  #     """
  # },
  # {
  #     "id": "SI-SINT",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per Source IP",
  #     "description": "Standard deviation of packet inter-arrival times per source IP",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_srcip_stateful_std_interarrival_topnvalue",
  #       "flow_srcip_stateful_std_interarrival_distribution"
  #     ],

  #     "sql": """
  #       SELECT
  #           srcip,
  #           STDDEV_POP(gap) AS std_iat
  #       FROM {table_name}_srcip_gaps
  #       WHERE gap IS NOT NULL
  #       GROUP BY srcip
  #       ORDER BY std_iat DESC
  #     """
  # },
  # {
  #     "id": "SI-CINT",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per Source IP",
  #     "description": "Coefficient of variation of packet inter-arrival times per source IP",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_srcip_stateful_cv_interarrival_topnvalue",
  #       "flow_srcip_stateful_cv_interarrival_distribution"
  #     ],

  #     "sql": """
  #       SELECT
  #           srcip,
  #           STDDEV_POP(gap) / AVG(gap) AS cv_iat
  #       FROM {table_name}_srcip_gaps
  #       WHERE gap IS NOT NULL
  #       GROUP BY srcip
  #       HAVING AVG(gap) > 0
  #       ORDER BY cv_iat DESC
  #     """
  # },

  # # Per Destination IP
  
  # {
  #     "id": "DI-AINT",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per Destination IP",
  #     "description": "Average packet inter-arrival time per destination IP (destination IPs with more than 10 packets)",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_dstip_stateful_avgpacketinterval_topnvalue",
  #       "flow_dstip_stateful_avgpacketinterval_distribution"
  #     ],

  #     "sql": """
  #       SELECT
  #           dstip,
  #           AVG(gap) AS avg_interval
  #       FROM {table_name}_dstip_gaps
  #       GROUP BY dstip
  #       HAVING COUNT(*) > 1
  #       ORDER BY avg_interval DESC
  #     """
  # },
  # {
  #     "id": "DI-DUR",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per Destination IP",
  #     "description": "Flow duration per destination IP",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_dstip_stateful_flowduration_topnvalue",
  #       "flow_dstip_stateful_flowduration_distribution"
  #     ],

  #     "sql": """
  #     SELECT dstip, MAX(time) - MIN(time) AS duration
  #     FROM {table_name}
  #     GROUP BY dstip
  #     ORDER BY duration DESC
  #     """
  # },
  # {
  #     "id": "DI-BRATE",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per Destination IP",
  #     "description": "Byte rate per destination IP",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_dstip_stateful_byterate_topnvalue",
  #       "flow_dstip_stateful_byterate_distribution"
  #     ],

  #     "sql": """
  #     SELECT dstip,
  #           SUM(pkt_len) /
  #           CASE
  #               WHEN MAX(time) - MIN(time) = 0 THEN 1
  #               ELSE MAX(time) - MIN(time)
  #           END AS byte_rate
  #     FROM {table_name}
  #     GROUP BY dstip
  #     HAVING COUNT(*) > 1
  #     ORDER BY byte_rate DESC
  #     """
  # },
  # {
  #     "id": "DI-SINT",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per Destination IP",
  #     "description": "Standard deviation of packet inter-arrival times per destination IP",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_dstip_stateful_std_interarrival_topnvalue",
  #       "flow_dstip_stateful_std_interarrival_distribution"
  #     ],

  #     "sql": """
  #       SELECT
  #           dstip,
  #           STDDEV_POP(gap) AS std_iat
  #       FROM {table_name}_dstip_gaps
  #       WHERE gap IS NOT NULL
  #       GROUP BY dstip
  #       ORDER BY std_iat DESC
  #     """
  # },
  # {
  #     "id": "DI-CINT",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per Destination IP",
  #     "description": "Coefficient of variation of packet inter-arrival times per destination IP",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_dstip_stateful_cv_interarrival_topnvalue",
  #       "flow_dstip_stateful_cv_interarrival_distribution"
  #     ],

  #     "sql": """
  #       SELECT
  #           dstip,
  #           STDDEV_POP(gap) / NULLIF(AVG(gap), 0) AS cv_iat
  #       FROM {table_name}_dstip_gaps
  #       WHERE gap IS NOT NULL
  #       GROUP BY dstip
  #       HAVING AVG(gap) > 0
  #       ORDER BY cv_iat DESC
  #     """
  # },

  # # Per IP Pair

  # {
  #     "id": "PR-AINT",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per IP Pair",
  #     "description": "Average packet inter-arrival time per source-destination IP pair (pairs with more than 10 packets)",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_ippair_stateful_avgpacketinterval_topnvalue",
  #       "flow_ippair_stateful_avgpacketinterval_distribution"
  #     ],

  #     "sql": """
  #       SELECT
  #           srcip,
  #           dstip,
  #           AVG(gap) AS avg_interval
  #       FROM {table_name}_ippair_gaps
  #       GROUP BY srcip, dstip
  #       HAVING COUNT(*) > 1
  #       ORDER BY avg_interval DESC
  #     """
  # },
  # {
  #     "id": "PR-DUR",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per IP Pair",
  #     "description": "Flow duration per source-destination IP pair",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_ippair_stateful_flowduration_topnvalue",
  #       "flow_ippair_stateful_flowduration_distribution"
  #     ],

  #     "sql": """
  #     SELECT srcip, dstip, MAX(time) - MIN(time) AS duration
  #     FROM {table_name}
  #     GROUP BY srcip, dstip
  #     ORDER BY duration DESC
  #     """
  # },
  # {
  #     "id": "PR-BRATE",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per IP Pair",
  #     "description": "Byte rate per source-destination IP pair",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_ippair_stateful_byterate_topnvalue",
  #       "flow_ippair_stateful_byterate_distribution"
  #     ],

  #     "sql": """
  #     SELECT srcip,
  #           dstip,
  #           SUM(pkt_len) /
  #           CASE
  #               WHEN MAX(time) - MIN(time) = 0 THEN 1
  #               ELSE MAX(time) - MIN(time)
  #           END AS byte_rate
  #     FROM {table_name}
  #     GROUP BY srcip, dstip
  #     HAVING COUNT(*) > 1
  #     ORDER BY byte_rate DESC
  #     """
  # },
  # {
  #     "id": "PR-SINT",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per IP Pair",
  #     "description": "Standard deviation of packet inter-arrival times per source-destination IP pair",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_ippair_stateful_std_interarrival_topnvalue",
  #       "flow_ippair_stateful_std_interarrival_distribution"
  #     ],

  #     "sql": """
  #       SELECT
  #           srcip,
  #           dstip,
  #           STDDEV_POP(gap) AS std_iat
  #       FROM {table_name}_ippair_gaps
  #       WHERE gap IS NOT NULL
  #       GROUP BY srcip, dstip
  #       ORDER BY std_iat DESC
  #     """
  # },
  # {
  #     "id": "PR-CINT",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per IP Pair",
  #     "description": "Coefficient of variation of packet inter-arrival times per source-destination IP pair",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_ippair_stateful_cv_interarrival_topnvalue",
  #       "flow_ippair_stateful_cv_interarrival_distribution"
  #     ],

  #     "sql": """
  #       SELECT
  #           srcip,
  #           dstip,
  #           STDDEV_POP(gap) / AVG(gap) AS cv_iat
  #       FROM {table_name}_ippair_gaps
  #       WHERE gap IS NOT NULL
  #       GROUP BY srcip, dstip
  #       HAVING AVG(gap) > 0
  #       ORDER BY cv_iat DESC
  #     """
  # },

  # # Per 5-Tuple Flow
  
  # {
  #     "id": "FT-AINT",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per 5-Tuple Flow",
  #     "description": "Average packet inter-arrival time per 5-tuple flow (flows with more than 10 packets)",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_fivetuple_stateful_avgpacketinterval_topnvalue",
  #       "flow_fivetuple_stateful_avgpacketinterval_distribution"
  #     ],

  #     "sql": """
  #       SELECT srcip, dstip, srcport, dstport, proto, AVG(gap) AS avg_interval
  #       FROM {table_name}_fivetuple_gaps
  #       GROUP BY srcip, dstip, srcport, dstport, proto
  #       HAVING COUNT(*) > 1
  #       ORDER BY avg_interval DESC
  #     """
  # },
  # {
  #     "id": "FT-DUR",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per 5-Tuple Flow",
  #     "description": "Flow duration per 5-tuple flow",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_fivetuple_stateful_flowduration_topnvalue",
  #       "flow_fivetuple_stateful_flowduration_distribution"
  #     ],

  #     "sql": """
  #     SELECT srcip, dstip, srcport, dstport, proto, MAX(time) - MIN(time) AS duration
  #     FROM {table_name}
  #     GROUP BY srcip, dstip, srcport, dstport, proto
  #     ORDER BY duration DESC
  #     """
  # },
  # {
  #     "id": "FT-BRATE",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per 5-Tuple Flow",
  #     "description": "Byte rate per 5-tuple flow",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_fivetuple_stateful_byterate_distribution"
  #     ],

  #     "sql": """
  #     SELECT srcip, dstip, srcport, dstport, proto,
  #           SUM(pkt_len) /
  #           CASE
  #               WHEN MAX(time) - MIN(time) = 0 THEN 1
  #               ELSE MAX(time) - MIN(time)
  #           END AS byte_rate
  #     FROM {table_name}
  #     GROUP BY srcip, dstip, srcport, dstport, proto
  #     HAVING COUNT(*) > 1
  #     ORDER BY byte_rate DESC
  #     """
  # },
  # {
  #     "id": "FT-BRATE",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per 5-Tuple Flow",
  #     "description": "Byte rate per 5-tuple flow",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_fivetuple_stateful_byterate_topnvalue",
  #     ],

  #     "sql": """
  #     SELECT srcip, dstip, srcport, dstport, proto,
  #           SUM(pkt_len) /
  #           CASE
  #               WHEN MAX(time) - MIN(time) = 0 THEN 1
  #               ELSE MAX(time) - MIN(time)
  #           END AS byte_rate
  #     FROM {table_name}
  #     GROUP BY srcip, dstip, srcport, dstport, proto
  #     ORDER BY byte_rate DESC
  #     """
  # },
  # {
  #     "id": "FT-SINT",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per 5-Tuple Flow",
  #     "description": "Standard deviation of packet inter-arrival times per 5-tuple flow",
  #     "category": "flow_level_stateful",
      
  #     "metric": [
  #       "flow_fivetuple_stateful_std_interarrival_topnvalue",
  #       "flow_fivetuple_stateful_std_interarrival_distribution"
  #     ],

  #     "sql": """
  #       SELECT srcip, dstip, srcport, dstport, proto, STDDEV_POP(gap) AS std_iat
  #       FROM {table_name}_fivetuple_gaps
  #       WHERE gap IS NOT NULL
  #       GROUP BY srcip, dstip, srcport, dstport, proto
  #       ORDER BY std_iat DESC
  #     """
  # },
  # {
  #     "id": "FT-CINT",
  #     "section": "Flow Level Stateful",
  #     "sub_section": "Per 5-Tuple Flow",
  #     "description": "Coefficient of variation of packet inter-arrival times per 5-tuple flow",
  #     "category": "flow_level_stateful",

  #     "metric": [
  #       "flow_fivetuple_stateful_cv_interarrival_topnvalue",
  #       "flow_fivetuple_stateful_cv_interarrival_distribution"
  #     ],

  #     "sql": """
  #       SELECT srcip, dstip, srcport, dstport, proto, STDDEV_POP(gap) / AVG(gap) AS cv_iat
  #       FROM {table_name}_fivetuple_gaps
  #       WHERE gap IS NOT NULL
  #       GROUP BY srcip, dstip, srcport, dstport, proto
  #       HAVING AVG(gap) > 0
  #       ORDER BY cv_iat DESC
  #     """
  # },

]