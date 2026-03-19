from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_POLICIES_DIR = BASE_DIR / "policies"
CORE_INPUT_FIELDS = {
    "decision_id",
    "actor_id",
    "actor_role",
    "action",
    "resource",
    "amount",
    "risk_score",
    "evidence_score",
    "jurisdiction",
    "business_unit",
    "override_requested",
    "review_case_id",
    "policy_id",
    "policy_version",
    "outcome",
    "reasons",
}
NUMBER_PATTERN = re.compile(r"^-?\d+(?:\.\d+)?$")


@dataclass(frozen=True)
class PolicyRule:
    condition: str
    reason: str


@dataclass(frozen=True)
class ActorPolicy:
    role: str
    allowed_actions: list[str]
    max_amount: float
    can_override: bool


@dataclass(frozen=True)
class EvidenceConfig:
    min_score: float
    required_signals: list[str]


@dataclass(frozen=True)
class OverrideConfig:
    allowed_roles: list[str]
    requirements: list[str]


@dataclass(frozen=True)
class AuditConfig:
    log_fields: list[str]


@dataclass(frozen=True)
class RuntimePolicy:
    policy_id: str
    version: str
    domain: str
    business_units: list[str]
    description: str
    actors: dict[str, ActorPolicy]
    evidence: EvidenceConfig
    escalation_rules: list[PolicyRule]
    refusal_rules: list[PolicyRule]
    overrides: OverrideConfig
    audit: AuditConfig


@dataclass(frozen=True)
class PolicyFieldSpec:
    name: str
    field_type: str
    label: str
    source: str


def to_dict(model: Any) -> dict[str, Any]:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


def format_field_label(name: str) -> str:
    return name.replace("_", " ").replace(".", " ").title()


def infer_field_type(name: str, comparator: str | None = None, rhs: str | None = None) -> str:
    lowered_name = name.lower()
    lowered_rhs = (rhs or "").strip().lower()

    if lowered_rhs in {"true", "false"}:
        return "boolean"

    if rhs and NUMBER_PATTERN.match(rhs.strip()):
        return "number"

    if comparator in {">", ">=", "<", "<="}:
        return "number"

    if any(token in lowered_name for token in ("amount", "score", "increase", "exposure")):
        return "number"

    if any(token in lowered_name for token in ("status", "reason", "reference", "id", "result")):
        return "text"

    return "text"


def parse_condition(condition: str) -> tuple[str, str, str] | None:
    match = re.match(r"^\s*(.+?)\s*(>=|<=|!=|=|>|<)\s*(.+?)\s*$", condition)
    if not match:
        return None
    return match.group(1).strip(), match.group(2), match.group(3).strip()


def resolve_token(token: str, context: dict[str, Any]) -> Any:
    value = token.strip()
    lowered = value.lower()

    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if NUMBER_PATTERN.match(value):
        return float(value) if "." in value else int(value)

    current: Any = context
    if "." in value:
        for part in value.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return value
        return current

    return context.get(value, value)


def build_evaluation_context(decision, certificate, actor_policy: ActorPolicy | None) -> dict[str, Any]:
    decision_dict = to_dict(decision)
    decision_context = dict(decision_dict.get("context") or {})

    context: dict[str, Any] = {
        **decision_context,
        "decision_id": decision.decision_id,
        "actor_id": decision.actor_id,
        "actor_role": certificate.actor_role if certificate is not None else decision.actor_role,
        "action": decision.action,
        "resource": decision.resource,
        "amount": decision.amount,
        "risk_score": decision.risk_score,
        "evidence_score": decision.evidence_score,
        "jurisdiction": decision.jurisdiction,
        "business_unit": decision.business_unit,
        "override_requested": decision.override_requested,
        "review_case_id": decision.review_case_id,
        "actor_certificate_active": certificate.is_active if certificate is not None else None,
        "actor": {
            "id": certificate.actor_id if certificate is not None else decision.actor_id,
            "role": certificate.actor_role if certificate is not None else decision.actor_role,
            "max_amount": actor_policy.max_amount if actor_policy is not None else None,
            "can_override": actor_policy.can_override if actor_policy is not None else None,
        },
        "certificate": {
            "is_active": certificate.is_active if certificate is not None else None,
            "delegation_chain_valid": certificate.delegation_chain_valid if certificate is not None else None,
            "policy_anchor": certificate.policy_anchor if certificate is not None else None,
        },
    }
    return context


def evaluate_condition(condition: str, context: dict[str, Any]) -> bool:
    parsed = parse_condition(condition)
    if parsed is None:
        return False

    lhs_token, operator, rhs_token = parsed
    lhs_value = resolve_token(lhs_token, context)
    rhs_value = resolve_token(rhs_token, context)

    if operator == "=":
        return lhs_value == rhs_value
    if operator == "!=":
        return lhs_value != rhs_value

    if lhs_value is None or rhs_value is None:
        return False

    if operator == ">":
        return lhs_value > rhs_value
    if operator == ">=":
        return lhs_value >= rhs_value
    if operator == "<":
        return lhs_value < rhs_value
    if operator == "<=":
        return lhs_value <= rhs_value

    return False


def evaluate_rules(
    rules: list[PolicyRule],
    decision,
    certificate,
    actor_policy: ActorPolicy | None,
) -> list[str]:
    context = build_evaluation_context(decision, certificate, actor_policy)
    reasons: list[str] = []
    for rule in rules:
        if evaluate_condition(rule.condition, context):
            reasons.append(rule.reason)
    return reasons


class PolicyEngine:
    def __init__(self, policies_dir: str | Path | None = None) -> None:
        self.policies_dir = Path(policies_dir) if policies_dir is not None else DEFAULT_POLICIES_DIR
        self.index = self._load_index()
        self.policies = self._load_policies()
        self.policies_by_id = {policy.policy_id: policy for policy in self.policies}

    def _load_index(self) -> dict[str, Any]:
        return json.loads((self.policies_dir / "policy_index.json").read_text())

    def _load_policies(self) -> list[RuntimePolicy]:
        policies: list[RuntimePolicy] = []
        for entry in self.index.get("policies", []):
            payload = yaml.safe_load((self.policies_dir / entry["file"]).read_text())
            actors = {
                role: ActorPolicy(
                    role=role,
                    allowed_actions=actor_config.get("allowed_actions", []),
                    max_amount=float(actor_config.get("max_amount", 0)),
                    can_override=bool(actor_config.get("can_override", False)),
                )
                for role, actor_config in payload.get("actors", {}).items()
            }
            policy = RuntimePolicy(
                policy_id=payload["policy_id"],
                version=str(payload["version"]),
                domain=payload["domain"],
                business_units=list(payload.get("business_units", [])),
                description=payload.get("description", "").strip(),
                actors=actors,
                evidence=EvidenceConfig(
                    min_score=float(payload.get("evidence", {}).get("min_score", 0.0)),
                    required_signals=list(payload.get("evidence", {}).get("required_signals", [])),
                ),
                escalation_rules=[
                    PolicyRule(condition=rule["condition"], reason=rule["reason"])
                    for rule in payload.get("escalation_rules", [])
                ],
                refusal_rules=[
                    PolicyRule(condition=rule["condition"], reason=rule["reason"])
                    for rule in payload.get("refusal_rules", [])
                ],
                overrides=OverrideConfig(
                    allowed_roles=list(payload.get("overrides", {}).get("allowed_roles", [])),
                    requirements=list(payload.get("overrides", {}).get("requirements", [])),
                ),
                audit=AuditConfig(
                    log_fields=list(payload.get("audit", {}).get("log_fields", [])),
                ),
            )
            policies.append(policy)
        return policies

    def list_policies(self) -> list[RuntimePolicy]:
        return list(self.policies)

    def get_policy(self, policy_id: str) -> RuntimePolicy | None:
        return self.policies_by_id.get(policy_id)

    def get_config(self, action: str, business_unit: str) -> RuntimePolicy | None:
        for policy in self.policies:
            if business_unit not in policy.business_units:
                continue
            if any(action in actor.allowed_actions for actor in policy.actors.values()):
                return policy
        return None

    def list_actions(self) -> list[str]:
        return sorted(
            {
                action
                for policy in self.policies
                for actor in policy.actors.values()
                for action in actor.allowed_actions
            }
        )

    def list_business_units(self) -> list[str]:
        return sorted({business_unit for policy in self.policies for business_unit in policy.business_units})

    def get_field_specs(self, policy: RuntimePolicy) -> list[PolicyFieldSpec]:
        specs: dict[str, PolicyFieldSpec] = {}

        def add_spec(name: str, field_type: str, source: str) -> None:
            if name in CORE_INPUT_FIELDS:
                return
            if name.startswith("actor.") or name.startswith("certificate.") or name == "actor_certificate_active":
                return
            specs.setdefault(
                name,
                PolicyFieldSpec(
                    name=name,
                    field_type=field_type,
                    label=format_field_label(name),
                    source=source,
                ),
            )

        for signal in policy.evidence.required_signals:
            add_spec(signal, "boolean", "required_signal")

        for source_name, rules in (
            ("escalation_rule", policy.escalation_rules),
            ("refusal_rule", policy.refusal_rules),
        ):
            for rule in rules:
                parsed = parse_condition(rule.condition)
                if parsed is None:
                    continue
                lhs_token, comparator, rhs_token = parsed
                add_spec(lhs_token, infer_field_type(lhs_token, comparator, rhs_token), source_name)

        for requirement in policy.overrides.requirements:
            add_spec(requirement, "text", "override_requirement")

        for field_name in policy.audit.log_fields:
            add_spec(field_name, infer_field_type(field_name), "audit_field")

        return list(specs.values())
