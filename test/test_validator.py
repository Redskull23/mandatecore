import unittest
from copy import deepcopy

from app.models.decision import AIDecision
from app.models.outcome import AuthorityOutcome
from demo.scenarios import scenarios
from engine.audit import build_audit_entry
from engine.policy import PolicyEngine
from engine.registry import AuthorityRegistry
from engine.validator import MandateCoreValidator


def scenario_payload(name: str) -> dict:
    for scenario in scenarios:
        if scenario["name"] == name:
            return deepcopy(scenario["payload"])
    raise KeyError(name)


class MandateCoreValidatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = AuthorityRegistry()
        self.policy_engine = PolicyEngine()
        self.validator = MandateCoreValidator(self.registry, self.policy_engine)

    def build_decision(self, payload: dict) -> AIDecision:
        return AIDecision(**payload)

    def test_policy_engine_resolves_wire_policy(self) -> None:
        policy = self.policy_engine.get_config("approve_wire", "consumer_banking")
        self.assertIsNotNone(policy)
        self.assertEqual(policy.policy_id, "wire-transfer-controls")

    def test_allows_wire_decision_with_complete_context(self) -> None:
        decision = self.build_decision(scenario_payload("Allow: wire approval within AI mandate"))
        response = self.validator.validate(decision)
        self.assertEqual(response.outcome, AuthorityOutcome.ALLOW)
        self.assertEqual(response.policy_id, "wire-transfer-controls")

    def test_escalates_first_time_beneficiary_wire(self) -> None:
        decision = self.build_decision(scenario_payload("Escalate: first-time beneficiary wire"))
        response = self.validator.validate(decision)
        self.assertEqual(response.outcome, AuthorityOutcome.ESCALATE)
        self.assertIn("First-time beneficiary requires review", response.reasons)

    def test_refuses_wire_sanctions_hit(self) -> None:
        decision = self.build_decision(scenario_payload("Refuse: sanctions hit on wire"))
        response = self.validator.validate(decision)
        self.assertEqual(response.outcome, AuthorityOutcome.REFUSE)
        self.assertIn("Positive sanctions signal cannot auto-execute", response.reasons)

    def test_allows_credit_approval_within_threshold(self) -> None:
        decision = self.build_decision(
            scenario_payload("Allow: underwriting analyst approves modest increase")
        )
        response = self.validator.validate(decision)
        self.assertEqual(response.outcome, AuthorityOutcome.ALLOW)
        self.assertEqual(response.policy_id, "credit-line-increase-controls")

    def test_refuses_when_actor_has_no_certificate(self) -> None:
        payload = scenario_payload("Allow: wire approval within AI mandate")
        payload["actor_id"] = "unknown_actor"
        decision = self.build_decision(payload)
        response = self.validator.validate(decision)
        self.assertEqual(response.outcome, AuthorityOutcome.REFUSE)
        self.assertIn("No authority certificate found for actor.", response.reasons)

    def test_builds_demo_audit_entry_from_policy_fields(self) -> None:
        payload = scenario_payload("Allow: fraud analyst releases hold")
        decision = self.build_decision(payload)
        response = self.validator.validate(decision)
        policy = self.policy_engine.get_config(decision.action, decision.business_unit)
        certificate = self.registry.get_certificate(decision.actor_id)
        actor_policy = policy.actors.get(certificate.actor_role)

        audit_entry = build_audit_entry(decision, response, policy, certificate, actor_policy)

        self.assertEqual(audit_entry["policy_id"], "fraud-hold-release")
        self.assertEqual(audit_entry["account_id"], "deposit_account_1029")
        self.assertEqual(audit_entry["hold_reason"], "card_not_present_review")
        self.assertEqual(audit_entry["outcome"], "ALLOW")
        self.assertIn("event_ts", audit_entry)


if __name__ == "__main__":
    unittest.main()
