# Reference Evaluation Kit

## What problem does this demonstrate?

Authorization answers a point-in-time question: *may this actor begin?* It does not prove that the same execution remains lawful after delegated authority is revoked, evidence becomes stale, policy changes, or its runtime context changes.

DecisionAssure demonstrates a narrower, more useful proposition: **execution must remain continuously admissible throughout runtime**. It records the decision as signed governance evidence, then reconstructs authority, policy, evidence, and runtime context during replay.

This is a local reference implementation, not a product or a platform.

## Architecture

```text
Decision request → admission evaluation → immutable signed receipt
                         │                         │
                         │                         ├── GET /receipt/{id}
                         ▼                         ├── POST /verify
                  authority / policy /             └── POST /replay
                  evidence / runtime context                 │
                                                           reconstructs live conditions
```

```text
REQUESTED → AUTHORIZED → ADMISSIBLE → EXECUTING → CONTINUATION VERIFIED → COMPLETED
                   │            │                        │
                   └────────────┴────────────────────────┴──→ DENIED / CONTAINED
```

Sequence:

```text
Caller        Runtime                 Receipt store          Replay
  | POST /decision |                         |                 |
  |--------------->| evaluate all live facts |                 |
  |                |---- signed evidence --->|                 |
  |<---------------| receipt                 |                 |
  | POST /replay ----------------------------|---------------->|
  |<------------------------------------------------ reconstruct + decision
```

## Under-ten-minute evaluation

```sh
./evaluate.sh
```

The script builds and starts Docker, creates one decision, retrieves its receipt, runs every replay scenario, and proves that a stored receipt becomes invalid after tampering. It leaves the local service running; use `docker compose down` when finished.

## The five scenarios

| Scenario | Changed live condition | Result |
|---|---|---|
| 1 | None | PASS |
| 2 | Delegated authority revoked | FAIL — authority continuity lost |
| 3 | Evidence stale | FAIL — evidence freshness violated |
| 4 | Policy version changed | REVALIDATION REQUIRED |
| 5 | Material runtime context changed | CONTAINED |

## Repository overview

- `app/governance.py` is the admission orchestration and process-local in-memory receipt store.
- `app/authority.py`, `policy.py`, and `evidence.py` make the three eligibility dimensions explicit.
- `app/replay.py` reconstructs live governance facts and decides continuation.
- `app/receipt.py` produces canonical hashes and an HMAC signature.
- `app/verify.py` recomputes evidence and explains receipt tampering.
- `sample/` contains minimal request and replay-state payloads.

## API

Only five business endpoints exist: `POST /decision`, `GET /receipt/{id}`, `POST /replay`, `POST /verify`, and `POST /tamper`.

`receipt_id` is the one canonical identifier for `GET /receipt/{receipt_id}`, replay, and tampering. It is distinct from the caller-provided `decision_id` and from `receipt_signature`. The idempotency policy is **same `decision_id`, same receipt**: submitting an identical decision ID again returns the originally stored receipt.

`POST /decision` accepts [sample/valid_request.json](sample/valid_request.json), returning a receipt whose evidence includes:

```json
{
  "authorization_status": "VERIFIED",
  "admissibility_status": "PASS",
  "continuation_status": "VERIFIED",
  "state_trace": ["REQUESTED", "AUTHORIZED", "ADMISSIBLE", "EXECUTING", "CONTINUATION VERIFIED", "COMPLETED"]
}
```

Replay accepts a receipt ID and a current-state object. Each response includes `status`, a human-readable `reason`, and `state_transition`. An inactive authority or stale evidence yields `FAIL`; a policy change yields `REVALIDATION REQUIRED`; an unhealthy runtime (or changed context) yields `CONTAINED`.

`POST /tamper` intentionally changes one requested protected field in the stored receipt and returns its old and new values. It supports `policy_version`, `authority_id`, `runtime_context_hash`, `evidence_hash`, `execution_hash`, and `timestamp`. Submit its returned receipt as `{"receipt": <tampered receipt>}` to `POST /verify`; verification recomputes integrity and returns `VALID: false`, `reason: "signature mismatch"`, and `tampered_fields`.

## Architecture decisions

- **No persistence:** the receipt ledger is intentionally process-local to keep the focus on semantics, not infrastructure.
- **Deterministic time:** the request timestamp is supplied and defaults to a fixed value, producing reproducible evidence.
- **Explicit state trace:** states are evidence, not hidden control flow.
- **HMAC signature:** sufficient for local tamper demonstration; a production design would use managed asymmetric keys and external retention.
- **Replay is reconstruction:** it evaluates present authority, policy, evidence, and runtime facts; it is not a hash comparison.

## Limitations

This reference has no durable ledger, external identity proof, real policy engine, clock, distributed consistency controls, or key management. The `/tamper` endpoint exists only to demonstrate verification. Runtime facts are supplied as deterministic input rather than collected from a production environment.

## Future directions

Add an append-only external evidence store, signed authority attestations, policy-as-code evaluation, event-sourced context adapters, cryptographic key rotation, retention rules, and independently verifiable replay bundles.
