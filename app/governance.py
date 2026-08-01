"""The small orchestration layer for admission and in-memory receipt storage."""
from __future__ import annotations

from .authority import is_active
from .evidence import is_fresh
from .models import DecisionRequest, GovernanceReceipt, RuntimeState
from .receipt import canonical_hash, protected_field_hashes, seal
from .state_machine import AUTHORIZED, DENIED, REQUESTED, admitted_trace


class GovernanceRuntime:
    def __init__(self) -> None:
        self._receipts: dict[str, GovernanceReceipt] = {}
        self._decision_receipts: dict[str, str] = {}

    def decide(self, request: DecisionRequest, state: RuntimeState) -> GovernanceReceipt:
        trace = [REQUESTED]
        if not is_active(state):
            return self._store(self._receipt(request, trace + [DENIED], "DENIED", "DENIED", "NOT_EVALUATED", "DENIED", "Authorization absent: delegated authority is not active."))
        trace.append(AUTHORIZED)
        if not is_fresh(state) or not state.runtime_healthy:
            return self._store(self._receipt(request, trace + [DENIED], "VERIFIED", "DENIED", "NOT_EVALUATED", "DENIED", "Authorization exists, but current execution is not admissible."))
        return self._store(self._receipt(request, admitted_trace(), "VERIFIED", "PASS", "VERIFIED", "PASS", "Execution admitted and continuation verified."))

    def get(self, receipt_id: str) -> GovernanceReceipt | None:
        return self._receipts.get(receipt_id)

    def replace(self, receipt: GovernanceReceipt) -> None:
        """Replace a stored receipt only for the intentionally unsafe demo endpoint."""
        self._receipts[receipt.receipt_id] = receipt

    def _store(self, receipt: GovernanceReceipt) -> GovernanceReceipt:
        # Idempotency policy: a repeated decision_id returns its original receipt.
        existing_id = self._decision_receipts.get(receipt.decision_id)
        if existing_id is not None:
            return self._receipts[existing_id]
        self._receipts[receipt.receipt_id] = receipt
        self._decision_receipts[receipt.decision_id] = receipt.receipt_id
        return receipt

    @staticmethod
    def _receipt(request: DecisionRequest, trace: list[str], authorization: str, admissibility: str, continuation: str, replay_result: str, reason: str) -> GovernanceReceipt:
        snapshot = request.model_dump()
        values = {
            "authority_id": request.authority_id,
            "policy_version": request.policy_version,
            "runtime_context_hash": canonical_hash(request.runtime_context),
            "evidence_hash": canonical_hash({"evidence_id": request.evidence_id, "requested_at": request.requested_at}),
            "execution_hash": canonical_hash({"decision_id": request.decision_id, "authority_id": request.authority_id, "policy_version": request.policy_version}),
            "timestamp": request.requested_at,
            "request_snapshot": snapshot,
        }
        receipt = GovernanceReceipt(receipt_id=f"receipt-{request.decision_id}", decision_id=request.decision_id, authority_id=request.authority_id, policy_version=request.policy_version,
            runtime_context_hash=canonical_hash(request.runtime_context), evidence_hash=canonical_hash({"evidence_id": request.evidence_id, "requested_at": request.requested_at}),
            execution_hash=canonical_hash({"decision_id": request.decision_id, "authority_id": request.authority_id, "policy_version": request.policy_version}), timestamp=request.requested_at,
            authorization_status=authorization, admissibility_status=admissibility, continuation_status=continuation, receipt_signature="", replay_result=replay_result,
            decision_reason=reason, state_trace=trace, request_snapshot=snapshot,
            protected_field_hashes=protected_field_hashes(values))
        return seal(receipt)
