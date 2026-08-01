"""Replay reconstructs live governance conditions instead of comparing hashes."""
from .authority import is_active
from .evidence import is_fresh
from .models import GovernanceReceipt, RuntimeState
from .policy import is_current
from .receipt import canonical_hash
from .state_machine import CONTAINED, DENIED


def replay(receipt: GovernanceReceipt, state: RuntimeState) -> dict[str, object]:
    """Determine whether an already executing decision remains admissible."""
    reconstruction = {
        "authority": "active" if is_active(state) else "revoked",
        "policy": state.policy_version,
        "evidence": "fresh" if is_fresh(state) else "stale",
        "runtime": "healthy" if state.runtime_healthy else "unhealthy",
    }
    if not is_active(state):
        return _result("FAIL", "Authority continuity lost: delegated authority was revoked after execution began.", [DENIED], reconstruction)
    if not is_fresh(state):
        return _result("FAIL", "Evidence freshness violated: evidence became stale after execution began.", [DENIED], reconstruction)
    if not is_current(receipt, state):
        return _result("REVALIDATION REQUIRED", "Policy version changed; execution requires fresh admission under the current policy.", [DENIED], reconstruction)
    original_context = receipt.request_snapshot["runtime_context"]
    if not state.runtime_healthy:
        return _result("CONTAINED", "Runtime health degraded: execution has been contained.", [CONTAINED], reconstruction)
    if canonical_hash(state.runtime_context) != canonical_hash(original_context):
        return _result("CONTAINED", "Continuation no longer admissible: material runtime context changed.", [CONTAINED], reconstruction)
    return _result("PASS", "Authority, policy, evidence, and runtime context remain admissible.", ["CONTINUATION VERIFIED", "COMPLETED"], reconstruction)


def _result(result: str, reason: str, state_trace: list[str], reconstruction: dict[str, str]) -> dict[str, object]:
    return {
        "status": result,
        "replay_result": result,
        "reason": reason,
        "state_transition": state_trace,
        "state_trace": state_trace,
        "reconstructed": reconstruction,
    }
