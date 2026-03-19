from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from engine.policy import build_evaluation_context


def outcome_value(response) -> str:
    return response.outcome.value if hasattr(response.outcome, "value") else str(response.outcome)


def build_audit_entry(decision, response, policy, certificate, actor_policy=None) -> dict[str, Any]:
    context = build_evaluation_context(decision, certificate, actor_policy)
    entry: dict[str, Any] = {
        "event_ts": datetime.now(timezone.utc).isoformat(),
        "decision_id": decision.decision_id,
        "actor_id": decision.actor_id,
        "actor_role": certificate.actor_role if certificate is not None else decision.actor_role,
        "action": decision.action,
        "business_unit": decision.business_unit,
        "policy_id": response.policy_id or (policy.policy_id if policy is not None else None),
        "policy_version": response.policy_version or (policy.version if policy is not None else None),
        "outcome": outcome_value(response),
        "reasons": list(response.reasons),
    }

    if policy is None:
        return entry

    for field_name in policy.audit.log_fields:
        if field_name == "policy_id":
            entry[field_name] = policy.policy_id
            continue
        if field_name == "policy_version":
            entry[field_name] = policy.version
            continue
        if field_name == "outcome":
            entry[field_name] = outcome_value(response)
            continue
        if field_name == "actor_role" and certificate is not None:
            entry[field_name] = certificate.actor_role
            continue
        entry[field_name] = context.get(field_name)

    return entry
