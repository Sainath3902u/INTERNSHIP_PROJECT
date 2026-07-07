FLOW_STATELESS = [

    # Per Source IP

    {
        "id": "SI-PKT",
        "section": "Flow Level Stateless",
        "sub_section": "Per Source IP",
        "description": "Number of packets per source IP",
        "category": "flow_level_stateless",

        "metric": [
            "flow_srcip_stateless_packet_topnvalue"
        ],

        "sql": "SELECT srcip, COUNT(*) AS pkts FROM {table_name} GROUP BY srcip ORDER BY pkts DESC"
    },
    # {
    #     "id": "SI-BYTE",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per Source IP",
    #     "description": "Total bytes per source IP",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_srcip_stateless_bytes_topnvalue",
    #         "flow_srcip_stateless_bytes_distribution"
    #     ],

    #     "sql": "SELECT srcip, SUM(pkt_len) AS bytes FROM {table_name} GROUP BY srcip ORDER BY bytes DESC"
    # },
    # {
    #     "id": "SI-CD-SRCPORT",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per Source IP",
    #     "description": "Distinct source ports per source IP",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_srcip_stateless_connection2srcport_topnvalue",
    #         "flow_srcip_stateless_connection2srcport_distribution"
    #     ],

    #     "sql": "SELECT srcip, COUNT(DISTINCT srcport) AS n FROM {table_name} GROUP BY srcip ORDER BY n DESC"
    # },
    # {
    #     "id": "SI-CD-DSTIP",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per Source IP",
    #     "description": "Distinct destination IPs contacted per source IP",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_srcip_stateless_connection2dstip_topnvalue",
    #         "flow_srcip_stateless_connection2dstip_distribution"
    #     ],

    #     "sql": "SELECT srcip, COUNT(DISTINCT dstip) AS n FROM {table_name} GROUP BY srcip ORDER BY n DESC"
    # },
    # {
    #     "id": "SI-CD-DSTPORT",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per Source IP",
    #     "description": "Distinct destination ports contacted per source IP",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_srcip_stateless_connection2dstport_topnvalue",
    #         "flow_srcip_stateless_connection2dstport_distribution"
    #     ],

    #     "sql": "SELECT srcip, COUNT(DISTINCT dstport) AS n FROM {table_name} GROUP BY srcip ORDER BY n DESC"
    # },
    # {
    #     "id": "SI-CD-DSTIPPORT",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per Source IP",
    #     "description": "Distinct destination IP and destination port pairs contacted per source IP",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_srcip_stateless_connection2dstipport_topnvalue",
    #         "flow_srcip_stateless_connection2dstipport_distribution"
    #     ],

    #     "sql": "SELECT srcip, COUNT(DISTINCT (dstip, dstport)) AS n FROM {table_name} GROUP BY srcip ORDER BY n DESC"
    # },
    # {
    #     "id": "SI-CD-FLOW",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per Source IP",
    #     "description": "Distinct 5-tuple flows per source IP",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_srcip_stateless_connection2flow_topnvalue",
    #         "flow_srcip_stateless_connection2flow_distribution"
    #     ],

    #     "sql": "SELECT srcip, COUNT(DISTINCT (srcip, dstip, srcport, dstport, proto)) AS n FROM {table_name} GROUP BY srcip ORDER BY n DESC"
    # },

    # # Per Destination IP
    
    # {
    #     "id": "DI-PKT",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per Destination IP",
    #     "description": "Number of packets per destination IP",
    #     "category": "flow_level_stateless",

    #     "metric": [
    #         "flow_dstip_stateless_packet_topnvalue"
    #         ],

    #     "sql": "SELECT dstip, COUNT(*) AS pkts FROM {table_name} GROUP BY dstip ORDER BY pkts DESC"
    # },
    # {
    #     "id": "DI-BYTE",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per Destination IP",
    #     "description": "Total bytes per destination IP",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_dstip_stateless_bytes_topnvalue",
    #         "flow_dstip_stateless_bytes_distribution"
    #     ],

    #     "sql": "SELECT dstip, SUM(pkt_len) AS bytes FROM {table_name} GROUP BY dstip ORDER BY bytes DESC"
    # },
    # {
    #     "id": "DI-CD-DSTPORT",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per Destination IP",
    #     "description": "Distinct destination ports per destination IP",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_dstip_stateless_connection2dstport_topnvalue",
    #         "flow_dstip_stateless_connection2dstport_distribution"
    #     ],

    #     "sql": "SELECT dstip, COUNT(DISTINCT dstport) AS n FROM {table_name} GROUP BY dstip ORDER BY n DESC"
    # },
    # {
    #     "id": "DI-CD-SRCIP",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per Destination IP",
    #     "description": "Distinct source IPs contacting each destination IP",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_dstip_stateless_connection2srcip_topnvalue",
    #         "flow_dstip_stateless_connection2srcip_distribution"
    #     ],

    #     "sql": "SELECT dstip, COUNT(DISTINCT srcip) AS n FROM {table_name} GROUP BY dstip ORDER BY n DESC"
    # },
    # {
    #     "id": "DI-CD-SRCPORT",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per Destination IP",
    #     "description": "Distinct source ports per destination IP",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_dstip_stateless_connection2srcport_topnvalue",
    #         "flow_dstip_stateless_connection2srcport_distribution"
    #     ],

    #     "sql": "SELECT dstip, COUNT(DISTINCT srcport) AS n FROM {table_name} GROUP BY dstip ORDER BY n DESC"
    # },
    # {
    #     "id": "DI-CD-SRCIPPORT",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per Destination IP",
    #     "description": "Distinct source IP and source port pairs per destination IP",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_dstip_stateless_connection2srcipport_topnvalue",
    #         "flow_dstip_stateless_connection2srcipport_distribution"
    #     ],

    #     "sql": "SELECT dstip, COUNT(DISTINCT (srcip, srcport)) AS n FROM {table_name} GROUP BY dstip ORDER BY n DESC"
    # },
    # {
    #     "id": "DI-CD-FLOW",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per Destination IP",
    #     "description": "Distinct 5-tuple flows per destination IP",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_dstip_stateless_connection2flow_topnvalue",
    #         "flow_dstip_stateless_connection2flow_distribution"
    #     ],

    #     "sql": "SELECT dstip, COUNT(DISTINCT (srcip, dstip, srcport, dstport, proto)) AS n FROM {table_name} GROUP BY dstip ORDER BY n DESC"
    # },

    # # Per IP Pair
    
    # {
    #     "id": "PR-PKT",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per IP Pair",
    #     "description": "Number of packets per source-destination IP pair",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_ippair_stateless_packet_topnvalue",
    #         "flow_ippair_stateless_packet_distribution"
    #     ],

    #     "sql": "SELECT srcip, dstip, COUNT(*) AS pkts FROM {table_name} GROUP BY srcip, dstip ORDER BY pkts DESC"
    # },
    # {
    #     "id": "PR-BYTE",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per IP Pair",
    #     "description": "Total bytes per source-destination IP pair",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_ippair_stateless_bytes_topnvalue",
    #         "flow_ippair_stateless_bytes_distribution"
    #     ],

    #     "sql": "SELECT srcip, dstip, SUM(pkt_len) AS bytes FROM {table_name} GROUP BY srcip, dstip ORDER BY bytes DESC"
    # },
    # {
    #     "id": "PR-CD-SRCPORT",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per IP Pair",
    #     "description": "Distinct source ports per source-destination IP pair",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_ippair_stateless_connection2srcport_topnvalue",
    #         "flow_ippair_stateless_connection2srcport_distribution"
    #     ],

    #     "sql": "SELECT srcip, dstip, COUNT(DISTINCT srcport) AS n FROM {table_name} GROUP BY srcip, dstip ORDER BY n DESC"
    # },
    # {
    #     "id": "PR-CD-DSTPORT",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per IP Pair",
    #     "description": "Distinct destination ports per source-destination IP pair",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_ippair_stateless_connection2dstport_topnvalue",
    #         "flow_ippair_stateless_connection2dstport_distribution"
    #     ],

    #     "sql": "SELECT srcip, dstip, COUNT(DISTINCT dstport) AS n FROM {table_name} GROUP BY srcip, dstip ORDER BY n DESC"
    # },
    # {
    #     "id": "PR-CD-FLOW",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per IP Pair",
    #     "description": "Distinct 5-tuple flows per source-destination IP pair",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_ippair_stateless_connection2flow_topnvalue",
    #         "flow_ippair_stateless_connection2flow_distribution"
    #     ],

    #     "sql": "SELECT srcip, dstip, COUNT(DISTINCT (srcip, dstip, srcport, dstport, proto)) AS n FROM {table_name} GROUP BY srcip, dstip ORDER BY n DESC"
    # },

    # # Per 5-Tuple Flow
    
    # {
    #     "id": "FT-PKT",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per 5-Tuple Flow",
    #     "description": "Number of packets per 5-tuple flow",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_fivetuple_stateless_packet_topnvalue",
    #         "flow_fivetuple_stateless_packet_distribution"
    #     ],

    #     "sql": "SELECT srcip, dstip, srcport, dstport, proto, COUNT(*) AS pkts FROM {table_name} GROUP BY srcip, dstip, srcport, dstport, proto ORDER BY pkts DESC"
    # },
    # {
    #     "id": "FT-BYTE",
    #     "section": "Flow Level Stateless",
    #     "sub_section": "Per 5-Tuple Flow",
    #     "description": "Total bytes per 5-tuple flow",
    #     "category": "flow_level_stateless",
        
    #     "metric": [
    #         "flow_fivetuple_stateless_bytes_topnvalue",
    #         "flow_fivetuple_stateless_bytes_distribution"
    #     ],

    #     "sql": "SELECT srcip, dstip, srcport, dstport, proto, SUM(pkt_len) AS bytes FROM {table_name} GROUP BY srcip, dstip, srcport, dstport, proto ORDER BY bytes DESC"
    # }

]