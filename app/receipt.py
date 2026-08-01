"""Canonical, signed governance evidence; no application-log semantics."""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from .models import GovernanceReceipt

_SIGNING_KEY = b"decisionassure-reference-fixed-key"
PROTECTED_FIELDS = (
    "authority_id",
    "policy_version",
    "runtime_context_hash",
    "evidence_hash",
    "execution_hash",
    "timestamp",
    "request_snapshot",
)


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def signed_payload(receipt: GovernanceReceipt) -> dict[str, Any]:
    """Return the receipt evidence excluding its signature."""
    return receipt.model_dump(exclude={"receipt_signature"})


def sign(receipt: GovernanceReceipt) -> str:
    payload = json.dumps(signed_payload(receipt), sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(_SIGNING_KEY, payload, hashlib.sha256).hexdigest()


def seal(receipt: GovernanceReceipt) -> GovernanceReceipt:
    return receipt.model_copy(update={"receipt_signature": sign(receipt)})


def protected_field_hashes(receipt_values: dict[str, Any]) -> dict[str, str]:
    """Create stable field fingerprints for a useful tamper report."""
    return {field: canonical_hash(receipt_values[field]) for field in PROTECTED_FIELDS}
