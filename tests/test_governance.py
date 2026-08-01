import unittest

from app.governance import GovernanceRuntime
from app.models import RuntimeState
from app.replay import replay
from app.sample_data import healthy_state, valid_request
from app.verify import verify


class RuntimeGovernanceTests(unittest.TestCase):
    def setUp(self):
        self.runtime = GovernanceRuntime()
        self.receipt = self.runtime.decide(valid_request(), healthy_state())

    def test_admitted_execution_replays(self):
        self.assertEqual(replay(self.receipt, healthy_state())["replay_result"], "PASS")

    def test_revoked_authority_fails_continuity(self):
        self.assertEqual(replay(self.receipt, RuntimeState(authority_active=False))["replay_result"], "FAIL")

    def test_stale_evidence_fails(self):
        self.assertEqual(replay(self.receipt, RuntimeState(evidence_fresh=False))["replay_result"], "FAIL")

    def test_changed_policy_requires_revalidation(self):
        self.assertEqual(replay(self.receipt, RuntimeState(policy_version="new"))["replay_result"], "REVALIDATION REQUIRED")

    def test_changed_context_is_contained(self):
        self.assertEqual(replay(self.receipt, RuntimeState(runtime_context={"risk_tier": "high"}))["replay_result"], "CONTAINED")

    def test_unhealthy_runtime_is_contained(self):
        result = replay(self.receipt, RuntimeState(runtime_healthy=False))
        self.assertEqual(result["status"], "CONTAINED")
        self.assertIn("Runtime health degraded", result["reason"])

    def test_signature_detects_tampering(self):
        altered = self.receipt.model_copy(update={"policy_version": "altered"})
        report = verify(altered)
        self.assertFalse(report["valid"])
        self.assertFalse(report["VALID"])
        self.assertIn("policy_version", report["tampered_fields"])
        self.assertIn("receipt_signature does not match receipt content", report["changes"])

    def test_repeated_decision_id_returns_the_same_receipt(self):
        repeated = self.runtime.decide(valid_request(), healthy_state())
        self.assertEqual(repeated.receipt_id, self.receipt.receipt_id)
        self.assertIs(self.runtime.get(self.receipt.receipt_id), self.receipt)


if __name__ == "__main__":
    unittest.main()
