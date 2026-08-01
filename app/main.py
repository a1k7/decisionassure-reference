"""Five endpoints, intentionally limited to governance demonstration behavior."""
from fastapi import FastAPI, HTTPException

from .governance import GovernanceRuntime
from .models import DecisionRequest, ReplayRequest, RuntimeState, TamperRequest, VerifyRequest
from .replay import replay
from .verify import verify

app = FastAPI(title="Reference Evaluation Kit", version="1.0.0")
runtime = GovernanceRuntime()


@app.post("/decision")
def decision(request: DecisionRequest):
    """Admit a request against the healthy baseline used by this reference."""
    return runtime.decide(request, RuntimeState())


@app.get("/receipt/{receipt_id}")
def receipt(receipt_id: str):
    found = runtime.get(receipt_id)
    if found is None:
        raise HTTPException(404, "Governance receipt not found")
    return found


@app.post("/replay")
def replay_receipt(request: ReplayRequest):
    found = runtime.get(request.receipt_id)
    if found is None:
        raise HTTPException(404, "Governance receipt not found")
    return replay(found, request.current_state)


@app.post("/verify")
def verify_receipt(request: VerifyRequest):
    return verify(request.receipt)


@app.post("/tamper")
def tamper(request: TamperRequest):
    found = runtime.get(request.receipt_id)
    if found is None:
        raise HTTPException(404, "Governance receipt not found")
    old_value = getattr(found, request.field)
    changed = found.model_copy(update={request.field: request.value})
    runtime.replace(changed)
    return {"receipt_id": changed.receipt_id, "field": request.field, "old_value": old_value, "new_value": request.value, "receipt": changed}
