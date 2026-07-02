from app.services.execution.base_executor import BaseRunner
from app.queries.flow_stateful_queries import FLOW_STATEFUL


class FlowStatefulRunner(BaseRunner):
    QUERIES = FLOW_STATEFUL