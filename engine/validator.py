from engine.evidence import EvidenceEvaluator
from app.models.outcome import AuthorityOutcome, ValidationResponse

class MandateCoreValidator:
    def __init__(self, registry, policy_engine) -> None:
        self.registry = registry
        self.policy_engine = policy_engine

    def validate(self, decision):
        reasons: list[str] = []
        cert = self.registry.get_certificate(decision.actor_id)

        if cert is None:
            return ValidationResponse(
                decision_id=decision.decision_id,
                outcome=AuthorityOutcome.REFUSE,
                reasons=["No authority certificate found for actor."],
            )

        policy = self.policy_engine.get_config(decision.action, decision.business_unit)

        if not cert.is_active:
            return ValidationResponse(
                decision_id=decision.decision_id,
                outcome=AuthorityOutcome.REFUSE,
                reasons=["Authority certificate is inactive."],
                policy_anchor=cert.policy_anchor,
            )

        if decision.action not in cert.permitted_actions:
            return ValidationResponse(
                decision_id=decision.decision_id,
                outcome=AuthorityOutcome.REFUSE,
                reasons=["Action is outside mandate scope."],
                policy_anchor=cert.policy_anchor,
            )

        if not cert.delegation_chain_valid:
            return ValidationResponse(
                decision_id=decision.decision_id,
                outcome=AuthorityOutcome.ESCALATE,
                reasons=["Delegation chain could not be validated."],
                policy_anchor=cert.policy_anchor,
            )

        if not EvidenceEvaluator.is_sufficient(
            decision.evidence_score,
            policy.min_evidence_score,
        ):
            return ValidationResponse(
                decision_id=decision.decision_id,
                outcome=AuthorityOutcome.ESCALATE,
                reasons=["Evidence is insufficient for execution."],
                policy_anchor=cert.policy_anchor,
            )

        if decision.override_requested and not cert.can_override:
            return ValidationResponse(
                decision_id=decision.decision_id,
                outcome=AuthorityOutcome.REFUSE,
                reasons=["Override requested by actor without override authority."],
                policy_anchor=cert.policy_anchor,
            )

        if decision.risk_score >= policy.refuse_risk_threshold:
            return ValidationResponse(
                decision_id=decision.decision_id,
                outcome=AuthorityOutcome.REFUSE,
                reasons=["Risk exceeds hard stop threshold."],
                policy_anchor=cert.policy_anchor,
            )

        if decision.risk_score >= policy.escalate_risk_threshold:
            reasons.append("Risk exceeds auto-approval threshold.")

        if decision.amount is not None and decision.amount > cert.max_amount:
            reasons.append("Requested amount exceeds delegated monetary authority.")

        if reasons:
            return ValidationResponse(
                decision_id=decision.decision_id,
                outcome=AuthorityOutcome.ESCALATE,
                reasons=reasons,
                policy_anchor=cert.policy_anchor,
            )

        return ValidationResponse(
            decision_id=decision.decision_id,
            outcome=AuthorityOutcome.ALLOW,
            reasons=["Decision passed runtime authority validation."],
            policy_anchor=cert.policy_anchor,
        )
