from engine.evidence import EvidenceEvaluator
from engine.policy import evaluate_rules
from app.models.outcome import AuthorityOutcome, ValidationResponse

class MandateCoreValidator:
    def __init__(self, registry, policy_engine) -> None:
        self.registry = registry
        self.policy_engine = policy_engine

    @staticmethod
    def _response(decision_id, outcome, reasons, policy=None, policy_anchor=None):
        return ValidationResponse(
            decision_id=decision_id,
            outcome=outcome,
            reasons=reasons,
            policy_anchor=policy.policy_id if policy is not None else policy_anchor,
            policy_id=policy.policy_id if policy is not None else None,
            policy_version=policy.version if policy is not None else None,
        )

    @staticmethod
    def _has_value(value) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != ""
        if isinstance(value, (list, tuple, dict, set)):
            return len(value) > 0
        return bool(value)

    @staticmethod
    def _dedupe(reasons: list[str]) -> list[str]:
        return list(dict.fromkeys(reasons))

    def validate(self, decision):
        reasons: list[str] = []
        cert = self.registry.get_certificate(decision.actor_id)

        if cert is None:
            return self._response(
                decision.decision_id,
                AuthorityOutcome.REFUSE,
                ["No authority certificate found for actor."],
            )

        policy = self.policy_engine.get_config(decision.action, decision.business_unit)
        if policy is None:
            return self._response(
                decision.decision_id,
                AuthorityOutcome.REFUSE,
                ["No matching YAML policy found for the selected action and business unit."],
                policy_anchor=cert.policy_anchor,
            )

        if not cert.is_active:
            return self._response(
                decision.decision_id,
                AuthorityOutcome.REFUSE,
                ["Authority certificate is inactive."],
                policy=policy,
            )

        if decision.actor_role != cert.actor_role:
            return self._response(
                decision.decision_id,
                AuthorityOutcome.REFUSE,
                ["Decision actor role does not match the authority certificate."],
                policy=policy,
            )

        actor_policy = policy.actors.get(cert.actor_role)
        if actor_policy is None:
            return self._response(
                decision.decision_id,
                AuthorityOutcome.REFUSE,
                ["Actor role is not eligible under the matched policy."],
                policy=policy,
            )

        if decision.action not in actor_policy.allowed_actions:
            return self._response(
                decision.decision_id,
                AuthorityOutcome.REFUSE,
                ["Action is outside the YAML policy scope for this actor role."],
                policy=policy,
            )

        if decision.override_requested:
            if cert.actor_role not in policy.overrides.allowed_roles or not actor_policy.can_override:
                return self._response(
                    decision.decision_id,
                    AuthorityOutcome.REFUSE,
                    ["Override requested by actor without override authority under the matched policy."],
                    policy=policy,
                )

            missing_override_requirements = [
                requirement
                for requirement in policy.overrides.requirements
                if not self._has_value(decision.context.get(requirement))
            ]
            if missing_override_requirements:
                reasons.append(
                    "Override request is missing required support: "
                    + ", ".join(missing_override_requirements)
                )

        refusal_reasons = evaluate_rules(policy.refusal_rules, decision, cert, actor_policy)
        if refusal_reasons:
            return self._response(
                decision.decision_id,
                AuthorityOutcome.REFUSE,
                self._dedupe(refusal_reasons),
                policy=policy,
            )

        if not cert.delegation_chain_valid:
            reasons.append("Delegation chain could not be validated.")

        if not EvidenceEvaluator.is_sufficient(
            decision.evidence_score,
            policy.evidence.min_score,
        ):
            reasons.append("Evidence score is below the minimum required by the matched policy.")

        missing_signals = [
            signal
            for signal in policy.evidence.required_signals
            if not self._has_value(decision.context.get(signal))
        ]
        if missing_signals:
            reasons.append(
                "Required evidence signals are missing or incomplete: "
                + ", ".join(missing_signals)
            )

        reasons.extend(evaluate_rules(policy.escalation_rules, decision, cert, actor_policy))

        if reasons:
            return self._response(
                decision.decision_id,
                AuthorityOutcome.ESCALATE,
                self._dedupe(reasons),
                policy=policy,
            )

        return self._response(
            decision.decision_id,
            AuthorityOutcome.ALLOW,
            ["Decision passed runtime authority validation against the matched YAML policy."],
            policy=policy,
        )
