"""HW6 adapter. No mock/offline fallback. seed is not supported by this API."""
from incident_agent.engine import investigate

def answer(question, seed=0):
    return investigate(question)["text"]


def preflight():
    from incident_agent.client import require_key
    require_key()


def metrics():
    from incident_agent.engine import LAST_METRICS
    return dict(LAST_METRICS)
