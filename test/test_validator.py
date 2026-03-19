import unittest

from app.models.decision import AIDecision
from app.models.outcome import AuthorityOutcome
from engine.policy import PolicyEngine
from engine.registry import AuthorityRegistry
from engine.validator import MandateCoreValidator


class MandateCoreValidatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = MandateCoreValidator(AuthorityRegistry(), PolicyEngine())

    def build_decision(self, **overrides) -> AIDecision:
        payload = {
            "decision_id": "dec-test",
            "actor_id": "ai_wire_agent",
            "actor_role": "ai_agent",
            "action": "approve_wire",
            "resource": "customer_account_8831",
            "amount": 5000.0,
            "risk_score": 0.22,
            "evidence_score": 0.93,
            "jurisdiction": "US",
            "business_unit": "consumer_banking",
            "override_requested": False,
        }
        payload.update(overrides)
        return AIDecision(**payload)

    def test_allows_low_risk_decision_within_mandate(self) -> None:
        response = self.validator.validate(self.build_decision())
        self.assertEqual(response.outcome, AuthorityOutcome.ALLOW)

    def test_escalates_when_amount_exceeds_authority(self) -> None:
        response = self.validator.validate(self.build_decision(amount=25000.0))
        self.assertEqual(response.outcome, AuthorityOutcome.ESCALATE)
        self.assertIn("Requested amount exceeds delegated monetary authority.", response.reasons)

    def test_escalates_when_evidence_is_insufficient(self) -> None:
        response = self.validator.validate(self.build_decision(evidence_score=0.54))
        self.assertEqual(response.outcome, AuthorityOutcome.ESCALATE)
        self.assertIn("Evidence is insufficient for execution.", response.reasons)

    def test_refuses_when_risk_exceeds_hard_stop_threshold(self) -> None:
        response = self.validator.validate(self.build_decision(risk_score=0.98))
        self.assertEqual(response.outcome, AuthorityOutcome.REFUSE)
        self.assertIn("Risk exceeds hard stop threshold.", response.reasons)

    def test_refuses_when_actor_has_no_certificate(self) -> None:
        response = self.validator.validate(self.build_decision(actor_id="unknown_actor"))
        self.assertEqual(response.outcome, AuthorityOutcome.REFUSE)
        self.assertIn("No authority certificate found for actor.", response.reasons)


if __name__ == "__main__":
    unittest.main()
