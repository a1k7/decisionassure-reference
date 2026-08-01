"""Run the five deterministic runtime-governance scenarios without typing curl."""
from app.governance import GovernanceRuntime
from app.models import RuntimeState
from app.replay import replay
from app.sample_data import healthy_state, valid_request


def run() -> None:
    runtime = GovernanceRuntime()
    receipt = runtime.decide(valid_request(), healthy_state())
    scenarios = [
        ("Scenario 1 — all admission conditions hold", healthy_state()),
        ("Scenario 2 — delegated authority revoked", RuntimeState(authority_active=False)),
        ("Scenario 3 — evidence becomes stale", RuntimeState(evidence_fresh=False)),
        ("Scenario 4 — policy version changes", RuntimeState(policy_version="2026.09")),
        ("Scenario 5 — material runtime context changes", RuntimeState(runtime_context={"region": "eu-west", "risk_tier": "high"})),
    ]
    print("Reference Evaluation Kit\n")
    print("Decision submitted | Authorization verified | Admission PASS | Receipt generated")
    print(f"Receipt: {receipt.receipt_id}\n")
    for name, state in scenarios:
        outcome = replay(receipt, state)
        print(name)
        print(f"Replay: {outcome['replay_result']}")
        print(f"Reason: {outcome['reason']}")
        print(f"State: {' → '.join(outcome['state_trace'])}\n")


if __name__ == "__main__":
    run()
