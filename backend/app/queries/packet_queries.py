PACKET_QUERIES = [

    # Global Packet Statistics

    {
        "id": "P-COUNT",
        "section": "Packet Level",
        "sub_section": "Global Packet Statistics",
        "description": "Total number of packets",
        "category": "packet_level",
        
        "metric": [
            "packet_stateless__count"
        ],

        "sql": "SELECT COUNT(*) AS total_packets FROM {table_name}"
    },
    {
        "id": "P-SRCIP-CD",
        "section": "Packet Level",
        "sub_section": "Global Packet Statistics",
        "description": "Number of distinct source IP addresses",
        "category": "packet_level",

        "metric": [
            "packet_stateless_srcip_countdistinct"
        ],

        "sql": "SELECT COUNT(DISTINCT srcip) AS n_src_ips FROM {table_name}"
    },
    {
        "id": "P-SRCIP-DIST",
        "section": "Packet Level",
        "sub_section": "Global Packet Statistics",
        "description": "Number of packets sent by each source IP",
        "category": "packet_level",

        "metric": [
            "packet_stateless_srcip_distribution"
        ],

        "sql": "SELECT srcip, COUNT(*) AS pkts FROM {table_name} GROUP BY srcip ORDER BY pkts DESC"
    },
    {
        "id": "P-DSTIP-CD",
        "section": "Packet Level",
        "sub_section": "Global Packet Statistics",
        "description": "Number of distinct destination IP addresses",
        "category": "packet_level",

        "metric": [
            "packet_stateless_dstip_countdistinct"
        ],

        "sql": "SELECT COUNT(DISTINCT dstip) AS n_dst_ips FROM {table_name}"
    },
    {
        "id": "P-DSTIP-DIST",
        "section": "Packet Level",
        "sub_section": "Global Packet Statistics",
        "description": "Number of packets received by each destination IP",
        "category": "packet_level",

        "metric": [
            "packet_stateless_dstip_distribution"
        ],

        "sql": "SELECT dstip, COUNT(*) AS pkts FROM {table_name} GROUP BY dstip ORDER BY pkts DESC"
    },
    {
        "id": "P-SRCPORT-CD",
        "section": "Packet Level",
        "sub_section": "Global Packet Statistics",
        "description": "Number of distinct source ports",
        "category": "packet_level",

        "metric": [
            "packet_stateless_srcport_countdistinct"
        ],
        
        "sql": "SELECT COUNT(DISTINCT srcport) AS n_src_ports FROM {table_name}"
    },
    {
        "id": "P-SRCPORT-DIST",
        "section": "Packet Level",
        "sub_section": "Global Packet Statistics",
        "description": "Packet distribution by source port",
        "category": "packet_level",

        "metric": [
            "packet_stateless_srcport_distribution"
        ],

        "sql": "SELECT srcport, COUNT(*) AS pkts FROM {table_name} GROUP BY srcport"
    },
    {
        "id": "P-DSTPORT-CD",
        "section": "Packet Level",
        "sub_section": "Global Packet Statistics",
        "description": "Number of distinct destination ports",
        "category": "packet_level",

        "metric": [
            "packet_stateless_dstport_countdistinct"
        ],
        
        "sql": "SELECT COUNT(DISTINCT dstport) AS n_dst_ports FROM {table_name}"
    },
    {
        "id": "P-DSTPORT-DIST",
        "section": "Packet Level",
        "sub_section": "Global Packet Statistics",
        "description": "Packet distribution by destination port",
        "category": "packet_level",

        "metric": [
            "packet_stateless_dstport_distribution"
        ],
 
        "sql": "SELECT dstport, COUNT(*) AS pkts FROM {table_name} GROUP BY dstport"
    },
    {
        "id": "P-PROTO-CD",
        "section": "Packet Level",
        "sub_section": "Global Packet Statistics",
        "description": "Number of distinct protocols",
        "category": "packet_level",

        "metric": [
            "packet_stateless_proto_countdistinct"
        ],

        "sql": "SELECT COUNT(DISTINCT proto) AS n_protocols FROM {table_name}"
    },
    {
        "id": "P-PROTO-DIST",
        "section": "Packet Level",
        "sub_section": "Global Packet Statistics",
        "description": "Packet distribution by protocol",
        "category": "packet_level",

        "metric": [
            "packet_stateless_proto_distribution"
        ],

        "sql": "SELECT proto, COUNT(*) AS pkts FROM {table_name} GROUP BY proto"
    },
    {
        "id": "P-TIME-DIST",
        "section": "Packet Level",
        "sub_section": "Global Packet Statistics",
        "description": "Packet timestamp distribution",
        "category": "packet_level",

        "metric": [
            "packet_stateless_time_distribution"
        ],

        "sql": """
        SELECT
            CAST(FLOOR(time / 1000000) AS BIGINT) AS bucket,
            COUNT(*) AS pkts
        FROM {table_name}
        GROUP BY bucket
        ORDER BY bucket
        """
    },
    {
        "id": "P-LEN-SUM",
        "section": "Packet Level",
        "sub_section": "Global Packet Statistics",
        "description": "Total packet bytes (sum of packet lengths)",
        "category": "packet_level",

        "metric": [
            "packet_stateless_pktlen_sum"
        ],

        "sql": "SELECT SUM(pkt_len) AS total_bytes FROM {table_name}"
    },
    {
        "id": "P-LEN-AVG",
        "section": "Packet Level",
        "sub_section": "Global Packet Statistics",
        "description": "Average packet length",
        "category": "packet_level",

        "metric": [
            "packet_stateless_pktlen_avg"
        ],

        "sql": "SELECT AVG(pkt_len) AS avg_pkt_len FROM {table_name}"
    },
    {
        "id": "P-LEN-DIST",
        "section": "Packet Level",
        "sub_section": "Global Packet Statistics",
        "description": "Packet length distribution",
        "category": "packet_level",

        "metric": [
            "packet_stateless_pktlen_distribution"
        ],

        "sql": """
        SELECT
            CAST(FLOOR(pkt_len / 1) * 1 AS INT) AS len_bucket,
            COUNT(*) AS pkts
        FROM {table_name}
        GROUP BY len_bucket
        ORDER BY len_bucket
        """
    }, 

    # Per Source Port Aggregations

    {
        "id": "SP-PKT",
        "section": "Packet Level",
        "sub_section": "Per Source Port Aggregations",
        "description": "Packet count per source port",
        "category": "packet_level",
        
        "metric": [
            "flow_srcport_stateless_packet_topnkey",
            "flow_srcport_stateless_packet_topnvalue"
        ],

        "sql": "SELECT srcport, COUNT(*) AS pkts FROM {table_name} GROUP BY srcport ORDER BY pkts DESC"
    },
    {
        "id": "SP-BYTE",
        "section": "Packet Level",
        "sub_section": "Per Source Port Aggregations",
        "description": "Total bytes per source port",
        "category": "packet_level",
        
        "metric": [
            "flow_srcport_stateless_bytes_topnkey", 
            "flow_srcport_stateless_bytes_topnvalue",
            "flow_srcport_stateless_bytes_distribution"
        ],
        
        "sql": "SELECT srcport, SUM(pkt_len) AS bytes FROM {table_name} GROUP BY srcport ORDER BY bytes DESC"
    },
    {
        "id": "SP-CD-SRCIP",
        "section": "Packet Level",
        "sub_section": "Per Source Port Aggregations",
        "description": "Distinct source IPs per source port",
        "category": "packet_level",
        
        "metric": [
            "flow_srcport_stateless_connection2srcip_topnkey", 
            "flow_srcport_stateless_connection2srcip_topnvalue",
            "flow_srcport_stateless_connection2srcip_distribution"
        ],

        "sql": "SELECT srcport, COUNT(DISTINCT srcip) AS n FROM {table_name} GROUP BY srcport ORDER BY n DESC"
    },
    {
        "id": "SP-CD-DSTIP",
        "section": "Packet Level",
        "sub_section": "Per Source Port Aggregations",
        "description": "Distinct destination IPs per source port",
        "category": "packet_level",
        
        "metric": [
            "flow_srcport_stateless_connection2dstip_topnkey", 
            "flow_srcport_stateless_connection2dstip_topnvalue",
            "flow_srcport_stateless_connection2dstip_distribution"
        ],

        "sql": "SELECT srcport, COUNT(DISTINCT dstip) AS n FROM {table_name} GROUP BY srcport ORDER BY n DESC"
    },
    {
        "id": "SP-CD-DSTPORT",
        "section": "Packet Level",
        "sub_section": "Per Source Port Aggregations",
        "description": "Distinct destination ports per source port",
        "category": "packet_level",
        
        "metric": [
            "flow_srcport_stateless_connection2dstport_topnkey", 
            "flow_srcport_stateless_connection2dstport_topnvalue",
            "flow_srcport_stateless_connection2dstport_distribution"
        ],

        "sql": "SELECT srcport, COUNT(DISTINCT dstport) AS n FROM {table_name} GROUP BY srcport ORDER BY n DESC, srcport ASC"
    },
    {
        "id": "SP-CD-DSTIPPORT",
        "section": "Packet Level",
        "sub_section": "Per Source Port Aggregations",
        "description": "Distinct `(dstip, dstport)` pairs per source port",
        "category": "packet_level",
        
        "metric": [
            "flow_srcport_stateless_connection2dstipport_topnkey", 
            "flow_srcport_stateless_connection2dstipport_topnvalue",
            "flow_srcport_stateless_connection2dstipport_distribution"
        ],
        
        "sql": "SELECT srcport, COUNT(DISTINCT (dstip, dstport)) AS n FROM {table_name} GROUP BY srcport ORDER BY n DESC"
    },
    {
        "id": "SP-CD-FLOW",
        "section": "Packet Level",
        "sub_section": "Per Source Port Aggregations",
        "description": "Distinct flows (5-tuples) per source port",
        "category": "packet_level",
        
        "metric": [
            "flow_srcport_stateless_connection2flow_topnkey", 
            "flow_srcport_stateless_connection2flow_topnvalue",
            "flow_srcport_stateless_connection2flow_distribution"
        ],

        "sql": """
            SELECT srcport,
                   COUNT(
                       DISTINCT (srcip, dstip, srcport, dstport, proto)
                   ) AS n
            FROM {table_name}
            GROUP BY srcport
            ORDER BY n DESC
        """
    },

    # Per Destination Port Aggregations

    {
        "id": "DP-PKT",
        "section": "Packet Level",
        "sub_section": "Per Destination Port Aggregations",
        "description": "Number of packets per destination port",
        "category": "packet_level",
        
        "metric": [
            "flow_dstport_stateless_packet_topnkey", 
            "flow_dstport_stateless_packet_topnvalue"
        ],

        "sql": "SELECT dstport, COUNT(*) AS pkts FROM {table_name} GROUP BY dstport ORDER BY pkts DESC"
    },
    {
        "id": "DP-BYTE",
        "section": "Packet Level",
        "sub_section": "Per Destination Port Aggregations",
        "description": "Total bytes per destination port",
        "category": "packet_level",
        
        "metric": [
            "flow_dstport_stateless_bytes_topnkey", 
            "flow_dstport_stateless_bytes_topnvalue",
            "flow_dstport_stateless_bytes_distribution"
        ],

        "sql": "SELECT dstport, SUM(pkt_len) AS bytes FROM {table_name} GROUP BY dstport ORDER BY bytes DESC"
    },
    {
        "id": "DP-CD-DSTIP",
        "section": "Packet Level",
        "sub_section": "Per Source Port Aggregations",
        "description": "Distinct Destination IPs per source port",
        "category": "packet_level",
        
        "metric": [
            "flow_dstport_stateless_connection2dstip_topnkey", 
            "flow_dstport_stateless_connection2dstip_topnvalue",
            "flow_dstport_stateless_connection2dstip_distribution"
        ],

        "sql": "SELECT dstport, COUNT(DISTINCT dstip) AS n FROM {table_name} GROUP BY dstport ORDER BY n DESC, dstport ASC"
    },
    {
        "id": "DP-CD-SRCIP",
        "section": "Packet Level",
        "sub_section": "Per Destination Port Aggregations",
        "description": "Distinct source IPs per destination port",
        "category": "packet_level",
        
        "metric": [
            "flow_dstport_stateless_connection2srcip_topnkey", 
            "flow_dstport_stateless_connection2srcip_topnvalue",
            "flow_dstport_stateless_connection2srcip_distribution"
        ],

        "sql": "SELECT dstport, COUNT(DISTINCT srcip) AS n FROM {table_name} GROUP BY dstport ORDER BY n DESC"
    },
    {
        "id": "DP-CD-SRCPORT",
        "section": "Packet Level",
        "sub_section": "Per Destination Port Aggregations",
        "description": "Distinct source ports per destination port",
        "category": "packet_level",
        
        "metric": [
            "flow_dstport_stateless_connection2srcport_topnkey", 
            "flow_dstport_stateless_connection2srcport_topnvalue",
            "flow_dstport_stateless_connection2srcport_distribution"
        ],

        "sql": "SELECT dstport, COUNT(DISTINCT srcport) AS n FROM {table_name} GROUP BY dstport ORDER BY n DESC"
    },
    {
        "id": "DP-CD-SRCIPPORT",
        "section": "Packet Level",
        "sub_section": "Per Destination Port Aggregations",
        "description": "Distinct `(srcip, srcport)` pairs per destination port",
        "category": "packet_level",
        
        "metric": [
            "flow_dstport_stateless_connection2srcipport_topnkey", 
            "flow_dstport_stateless_connection2srcipport_topnvalue",
            "flow_dstport_stateless_connection2srcipport_distribution"
        ],

        "sql": "SELECT dstport, COUNT(DISTINCT (srcip, srcport)) AS n FROM {table_name} GROUP BY dstport ORDER BY n DESC"
    },
    {
        "id": "DP-CD-FLOW",
        "section": "Packet Level",
        "sub_section": "Per Destination Port Aggregations",
        "description": "Distinct flows per destination port",
        "category": "packet_level",
        
         "metric": [
            "flow_dstport_stateless_connection2flow_topnkey", 
            "flow_dstport_stateless_connection2flow_topnvalue",
            "flow_dstport_stateless_connection2flow_distribution"
        ],

        "sql": """
            SELECT dstport,
                   COUNT(
                       DISTINCT (srcip, dstip, srcport, dstport, proto)
                   ) AS n
            FROM {table_name}
            GROUP BY dstport
            ORDER BY n DESC
        """
    }
]