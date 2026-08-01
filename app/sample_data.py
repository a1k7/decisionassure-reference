"""Deterministic values shared by the API examples and demonstration."""
from .models import DecisionRequest, RuntimeState


def valid_request(decision_id: str = "decision-demo-001") -> DecisionRequest:
    return DecisionRequest(decision_id=decision_id, authority_id="delegate-ops-17", policy_version="2026.08", evidence_id="evidence-case-42", runtime_context={"region": "eu-west", "risk_tier": "low"})


def healthy_state() -> RuntimeState:
    return RuntimeState()
