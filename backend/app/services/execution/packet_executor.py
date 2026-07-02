from app.services.execution.base_executor import BaseRunner
from app.queries.packet_queries import PACKET_QUERIES

class PacketRunner(BaseRunner):
    QUERIES = PACKET_QUERIES