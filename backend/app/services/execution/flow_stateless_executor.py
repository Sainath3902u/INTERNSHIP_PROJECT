from app.services.execution.base_executor import BaseRunner
from app.queries.flow_stateless_queries import FLOW_STATELESS


class FlowStatelessRunner(BaseRunner):
    QUERIES = FLOW_STATELESS