"""Integrity verification detects altered governance evidence."""
from .models import GovernanceReceipt
from .receipt import canonical_hash, sign


def verify(receipt: GovernanceReceipt) -> dict[str, object]:
    snapshot = receipt.request_snapshot
    expected_context = canonical_hash(snapshot["runtime_context"])
    expected_evidence = canonical_hash({"evidence_id": snapshot["evidence_id"], "requested_at": snapshot["requested_at"]})
    expected_execution = canonical_hash({"decision_id": receipt.decision_id, "authority_id": receipt.authority_id, "policy_version": receipt.policy_version})
    tampered_fields = [
        field for field, fingerprint in receipt.protected_field_hashes.items()
        if canonical_hash(getattr(receipt, field)) != fingerprint
    ]
    consistency_errors: list[str] = []
    if receipt.runtime_context_hash != expected_context:
        consistency_errors.append("runtime_context_hash")
    if receipt.evidence_hash != expected_evidence:
        consistency_errors.append("evidence_hash")
    if receipt.execution_hash != expected_execution:
        consistency_errors.append("execution_hash")
    if receipt.timestamp != snapshot["requested_at"]:
        consistency_errors.append("timestamp")
    for field in consistency_errors:
        if field not in tampered_fields:
            tampered_fields.append(field)
    signature_matches = receipt.receipt_signature == sign(receipt)
    valid = signature_matches and not tampered_fields
    return {
        "VALID": valid,
        "valid": valid,
        "result": "VALID" if valid else "TAMPERED",
        "reason": "No protected fields changed." if valid else "signature mismatch",
        "tampered_fields": tampered_fields,
        "changes": ["No changes detected."] if valid else ["signature mismatch", "receipt_signature does not match receipt content"],
    }
