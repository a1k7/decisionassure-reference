"""Typed boundary models for the deliberately small HTTP API."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class DecisionRequest(BaseModel):
    decision_id: str = Field(examples=["decision-demo-001"])
    authority_id: str = Field(examples=["delegate-ops-17"])
    policy_version: str = Field(examples=["2026.08"])
    evidence_id: str = Field(examples=["evidence-case-42"])
    runtime_context: dict[str, str] = Field(examples=[{"region": "eu-west", "risk_tier": "low"}])
    requested_at: str = "2026-08-01T09:00:00Z"


class RuntimeState(BaseModel):
    """The live facts used to re-evaluate a previously admitted execution."""

    authority_active: bool = True
    policy_version: str = "2026.08"
    evidence_fresh: bool = True
    runtime_context: dict[str, str] = Field(default_factory=lambda: {"region": "eu-west", "risk_tier": "low"})
    runtime_healthy: bool = True


class GovernanceReceipt(BaseModel):
    # This is the canonical identifier for retrieval, replay, and tampering.
    receipt_id: str
    decision_id: str
    authority_id: str
    policy_version: str
    runtime_context_hash: str
    evidence_hash: str
    execution_hash: str
    timestamp: str
    authorization_status: Literal["VERIFIED", "DENIED"]
    admissibility_status: Literal["PASS", "DENIED"]
    continuation_status: Literal["VERIFIED", "NOT_EVALUATED", "CONTAINED"]
    receipt_signature: str
    replay_result: str
    decision_reason: str
    state_trace: list[str]
    request_snapshot: dict[str, object]
    # Per-field digests make verification reports specific while the enclosing
    # receipt signature protects the complete receipt.
    protected_field_hashes: dict[str, str]


class ReplayRequest(BaseModel):
    receipt_id: str
    current_state: RuntimeState


class VerifyRequest(BaseModel):
    receipt: GovernanceReceipt


class TamperRequest(BaseModel):
    receipt_id: str
    field: Literal["policy_version", "authority_id", "runtime_context_hash", "evidence_hash", "execution_hash", "timestamp"] = "policy_version"
    value: str = "tampered"
