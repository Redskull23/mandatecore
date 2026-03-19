from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import streamlit as st

from app.models.decision import AIDecision
from demo.scenarios import scenarios
from engine.audit import build_audit_entry
from engine.policy import PolicyEngine, PolicyFieldSpec, RuntimePolicy, to_dict
from engine.registry import AuthorityRegistry
from engine.validator import MandateCoreValidator


def context_key(name: str) -> str:
    return f"context__{name}"


def get_default_payload() -> dict[str, Any]:
    return deepcopy(scenarios[0]["payload"])


@st.cache_resource
def get_runtime() -> tuple[AuthorityRegistry, PolicyEngine, MandateCoreValidator]:
    registry = AuthorityRegistry()
    policy_engine = PolicyEngine()
    validator = MandateCoreValidator(registry, policy_engine)
    return registry, policy_engine, validator


def load_payload(payload: dict[str, Any]) -> None:
    st.session_state["decision_id"] = payload["decision_id"]
    st.session_state["actor_id"] = payload["actor_id"]
    st.session_state["actor_role"] = payload["actor_role"]
    st.session_state["action"] = payload["action"]
    st.session_state["resource"] = payload["resource"]
    st.session_state["amount_enabled"] = payload.get("amount") is not None
    st.session_state["amount"] = float(payload["amount"]) if payload.get("amount") is not None else 0.0
    st.session_state["risk_score"] = float(payload["risk_score"])
    st.session_state["evidence_score"] = float(payload["evidence_score"])
    st.session_state["jurisdiction"] = payload["jurisdiction"]
    st.session_state["business_unit"] = payload["business_unit"]
    st.session_state["override_requested"] = payload["override_requested"]
    st.session_state["review_case_id"] = payload.get("review_case_id") or ""
    st.session_state["context_values"] = deepcopy(payload.get("context", {}))
    for key, value in st.session_state["context_values"].items():
        st.session_state[context_key(key)] = value
    st.session_state["last_payload"] = None
    st.session_state["last_response"] = None
    st.session_state["last_audit_entry"] = None
    st.session_state["last_error"] = None


def initialize_state() -> None:
    payload = get_default_payload()
    defaults = {
        "decision_id": payload["decision_id"],
        "actor_id": payload["actor_id"],
        "actor_role": payload["actor_role"],
        "action": payload["action"],
        "resource": payload["resource"],
        "amount_enabled": payload.get("amount") is not None,
        "amount": float(payload["amount"]) if payload.get("amount") is not None else 0.0,
        "risk_score": float(payload["risk_score"]),
        "evidence_score": float(payload["evidence_score"]),
        "jurisdiction": payload["jurisdiction"],
        "business_unit": payload["business_unit"],
        "override_requested": payload["override_requested"],
        "review_case_id": payload.get("review_case_id") or "",
        "context_values": deepcopy(payload.get("context", {})),
        "last_payload": None,
        "last_response": None,
        "last_audit_entry": None,
        "last_error": None,
        "audit_log": [],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    for key, value in st.session_state["context_values"].items():
        st.session_state.setdefault(context_key(key), value)


def default_context_value(spec: PolicyFieldSpec) -> Any:
    if spec.field_type == "boolean":
        return False
    if spec.field_type == "number":
        return 0.0
    return ""


def sync_context_defaults(field_specs: list[PolicyFieldSpec]) -> None:
    context_values = st.session_state.get("context_values", {})
    for spec in field_specs:
        st.session_state.setdefault(
            context_key(spec.name),
            context_values.get(spec.name, default_context_value(spec)),
        )


def build_context(field_specs: list[PolicyFieldSpec]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    for spec in field_specs:
        value = st.session_state.get(context_key(spec.name), default_context_value(spec))
        if spec.field_type == "text":
            if str(value).strip():
                context[spec.name] = str(value).strip()
            continue
        if spec.field_type == "number":
            context[spec.name] = float(value)
            continue
        context[spec.name] = bool(value)
    return context


def build_decision(field_specs: list[PolicyFieldSpec]) -> AIDecision:
    amount = float(st.session_state["amount"]) if st.session_state["amount_enabled"] else None
    return AIDecision(
        decision_id=st.session_state["decision_id"],
        actor_id=st.session_state["actor_id"],
        actor_role=st.session_state["actor_role"],
        action=st.session_state["action"],
        resource=st.session_state["resource"],
        amount=amount,
        risk_score=float(st.session_state["risk_score"]),
        evidence_score=float(st.session_state["evidence_score"]),
        jurisdiction=st.session_state["jurisdiction"],
        business_unit=st.session_state["business_unit"],
        override_requested=bool(st.session_state["override_requested"]),
        review_case_id=st.session_state["review_case_id"] or None,
        context=build_context(field_specs),
    )


def render_outcome(response: dict[str, Any]) -> None:
    outcome = response["outcome"]
    st.markdown(
        f"""
        <div class="outcome-card outcome-{outcome}">
            <div class="eyebrow">Validation outcome</div>
            <div class="outcome-value">{outcome}</div>
            <div>Policy: {response.get("policy_id") or "No policy matched"}</div>
            <div>Version: {response.get("policy_version") or "n/a"}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if outcome == "ALLOW":
        st.success("The decision can proceed within the delegated authority captured in the YAML policy.")
    elif outcome == "ESCALATE":
        st.warning("The decision needs additional review or evidence before execution.")
    else:
        st.error("The decision should not be executed under the matched policy.")

    st.markdown("#### Reasons")
    for reason in response["reasons"]:
        st.write(f"- {reason}")


def render_context_inputs(field_specs: list[PolicyFieldSpec]) -> None:
    if not field_specs:
        st.info("No additional policy-specific fields are required for the current selection.")
        return

    st.markdown("#### Policy Context")
    st.caption("These inputs are generated from the matched YAML policy's required signals, rules, overrides, and audit fields.")
    left_col, right_col = st.columns(2)

    for index, spec in enumerate(field_specs):
        target_col = left_col if index % 2 == 0 else right_col
        with target_col:
            widget_key = context_key(spec.name)
            help_text = f"Source: {spec.source.replace('_', ' ')}"
            if spec.field_type == "boolean":
                st.toggle(spec.label, key=widget_key, help=help_text)
            elif spec.field_type == "number":
                st.number_input(spec.label, key=widget_key, help=help_text, step=100.0)
            else:
                st.text_input(spec.label, key=widget_key, help=help_text)


def render_policy_summary(policy: RuntimePolicy | None, actor_role: str | None) -> None:
    st.subheader("Policy summary")
    if policy is None:
        st.warning("No YAML policy matches the current action and business unit.")
        return

    actor_policy = policy.actors.get(actor_role or "")
    st.markdown(f"**{policy.policy_id}**")
    st.caption(policy.description)
    summary_col_1, summary_col_2, summary_col_3 = st.columns(3)
    summary_col_1.metric("Min evidence", f"{policy.evidence.min_score:.2f}")
    summary_col_2.metric("Escalation rules", str(len(policy.escalation_rules)))
    summary_col_3.metric("Refusal rules", str(len(policy.refusal_rules)))

    if actor_policy is None:
        st.warning("The current actor role is not listed in this policy.")
    else:
        st.json(
            {
                "role": actor_policy.role,
                "allowed_actions": actor_policy.allowed_actions,
                "max_amount": actor_policy.max_amount,
                "can_override": actor_policy.can_override,
            },
            expanded=False,
        )


def render_audit_log(entries: list[dict[str, Any]]) -> None:
    st.subheader("Demo audit log")
    st.caption("This session log records each validation against the YAML-backed runtime policy flow.")

    if not entries:
        st.info("Run a validation to capture the first audit event.")
        return

    allow_count = sum(1 for entry in entries if entry["outcome"] == "ALLOW")
    escalate_count = sum(1 for entry in entries if entry["outcome"] == "ESCALATE")
    refuse_count = sum(1 for entry in entries if entry["outcome"] == "REFUSE")
    metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
    metric_col_1.metric("Allow", str(allow_count))
    metric_col_2.metric("Escalate", str(escalate_count))
    metric_col_3.metric("Refuse", str(refuse_count))

    table_rows = [
        {
            "event_ts": entry["event_ts"],
            "decision_id": entry["decision_id"],
            "policy_id": entry.get("policy_id"),
            "outcome": entry["outcome"],
            "actor_id": entry["actor_id"],
            "action": entry["action"],
            "review_case_id": entry.get("review_case_id"),
        }
        for entry in entries
    ]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    log_col_1, log_col_2 = st.columns([1, 1])
    with log_col_1:
        if st.button("Clear audit log", use_container_width=True):
            st.session_state["audit_log"] = []
            st.rerun()
    with log_col_2:
        st.download_button(
            "Download audit log JSON",
            data=json.dumps(entries, indent=2),
            file_name="mandatecore_audit_log.json",
            mime="application/json",
            use_container_width=True,
        )

    selected_entry = st.selectbox(
        "Inspect audit event",
        options=range(len(entries)),
        format_func=lambda index: f"{entries[index]['decision_id']} | {entries[index]['outcome']} | {entries[index]['policy_id']}",
    )
    st.json(entries[selected_entry], expanded=False)


def main() -> None:
    st.set_page_config(
        page_title="MandateCore Workbench",
        page_icon="MC",
        layout="wide",
    )

    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at top left, rgba(56, 189, 248, 0.18), transparent 28%),
                radial-gradient(circle at top right, rgba(249, 115, 22, 0.14), transparent 24%),
                linear-gradient(180deg, #07111f 0%, #0b1627 52%, #101a2f 100%);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0b1627 0%, #111f35 100%);
            border-right: 1px solid rgba(148, 163, 184, 0.16);
        }

        .block-container {
            max-width: 1280px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        [data-testid="stHeader"] {
            background: rgba(7, 17, 31, 0.72);
        }

        [data-testid="stAppViewContainer"] label,
        [data-testid="stAppViewContainer"] .stMarkdown,
        [data-testid="stAppViewContainer"] .stCaption,
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] .stCaption {
            color: #dbe7f5;
        }

        .hero {
            padding: 1.5rem;
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 24px;
            background:
                linear-gradient(135deg, rgba(15, 23, 42, 0.92) 0%, rgba(17, 31, 53, 0.9) 100%);
            backdrop-filter: blur(12px);
            box-shadow: 0 24px 60px rgba(2, 6, 23, 0.45);
            margin-bottom: 1rem;
        }

        .eyebrow {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #7dd3fc;
        }

        .hero-title {
            font-size: 2.2rem;
            font-weight: 700;
            color: #f8fafc;
            margin-top: 0.35rem;
        }

        .hero-copy {
            color: #cbd5e1;
            margin-top: 0.6rem;
            max-width: 60rem;
        }

        .outcome-card {
            border-radius: 24px;
            padding: 1.35rem 1.5rem;
            color: #ffffff;
            box-shadow: 0 24px 60px rgba(2, 6, 23, 0.38);
            margin-bottom: 1rem;
        }

        .outcome-ALLOW {
            background: linear-gradient(135deg, #115e59 0%, #0f766e 100%);
        }

        .outcome-ESCALATE {
            background: linear-gradient(135deg, #9a3412 0%, #ea580c 100%);
        }

        .outcome-REFUSE {
            background: linear-gradient(135deg, #991b1b 0%, #dc2626 100%);
        }

        .outcome-value {
            font-size: 2rem;
            font-weight: 700;
            margin-top: 0.35rem;
        }

        code {
            color: #e2e8f0;
            background: rgba(15, 23, 42, 0.9);
            padding: 0.15rem 0.35rem;
            border-radius: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    initialize_state()
    registry, policy_engine, validator = get_runtime()
    scenario_lookup = {scenario["name"]: deepcopy(scenario["payload"]) for scenario in scenarios}

    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">Runtime authority validation</div>
            <div class="hero-title">MandateCore Sample Policy Workbench</div>
            <div class="hero-copy">
                Run cross-domain banking decisions against the policy pack in <code>policies/</code>,
                inspect the matched controls, and capture a demo audit trail for every validation.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.subheader("Scenario presets")
        selected_scenario = st.selectbox("Choose a demo flow", list(scenario_lookup.keys()))
        if st.button("Load preset", use_container_width=True, type="primary"):
            load_payload(scenario_lookup[selected_scenario])
            st.rerun()

        if st.button("Reset to default", use_container_width=True):
            load_payload(get_default_payload())
            st.rerun()

        st.divider()
        st.subheader("Available policies")
        for policy in policy_engine.list_policies():
            st.markdown(f"**{policy.policy_id}**")
            st.caption(", ".join(policy.business_units))

    actor_ids = sorted(registry.certificates.keys())
    actions = sorted(set(policy_engine.list_actions()) | {st.session_state["action"]})
    business_units = sorted(set(policy_engine.list_business_units()) | {st.session_state["business_unit"]})

    input_col, context_col = st.columns([1.2, 1], gap="large")

    with input_col:
        st.subheader("Decision input")
        basic_col_1, basic_col_2 = st.columns(2)

        with basic_col_1:
            st.text_input("Decision ID", key="decision_id")
            st.selectbox("Actor ID", options=actor_ids, key="actor_id")
            certificate = registry.get_certificate(st.session_state["actor_id"])
            if certificate is not None:
                st.session_state["actor_role"] = certificate.actor_role
            st.text_input("Actor role", key="actor_role", disabled=True)
            st.selectbox("Action", options=actions, key="action")
            st.text_input("Resource", key="resource")
            st.text_input("Review case ID", key="review_case_id")

        with basic_col_2:
            st.selectbox("Business unit", options=business_units, key="business_unit")
            st.text_input("Jurisdiction", key="jurisdiction")
            st.toggle("Decision includes amount", key="amount_enabled")
            st.number_input(
                "Amount",
                min_value=0.0,
                step=500.0,
                format="%.2f",
                key="amount",
                disabled=not st.session_state["amount_enabled"],
            )
            st.slider("Risk score", min_value=0.0, max_value=1.0, step=0.01, key="risk_score")
            st.slider("Evidence score", min_value=0.0, max_value=1.0, step=0.01, key="evidence_score")
            st.toggle("Override requested", key="override_requested")

    current_policy = policy_engine.get_config(st.session_state["action"], st.session_state["business_unit"])
    current_field_specs = policy_engine.get_field_specs(current_policy) if current_policy is not None else []
    sync_context_defaults(current_field_specs)

    with context_col:
        render_policy_summary(current_policy, st.session_state["actor_role"])
        certificate = registry.get_certificate(st.session_state["actor_id"])
        st.subheader("Authority certificate")
        if certificate is None:
            st.warning("No certificate found for the selected actor.")
        else:
            st.json(to_dict(certificate), expanded=False)

    render_context_inputs(current_field_specs)

    if st.button("Validate decision", type="primary", use_container_width=True):
        try:
            decision = build_decision(current_field_specs)
            policy = policy_engine.get_config(decision.action, decision.business_unit)
            certificate = registry.get_certificate(decision.actor_id)
            actor_policy = policy.actors.get(certificate.actor_role) if policy is not None and certificate is not None else None
            response = validator.validate(decision)
            audit_entry = build_audit_entry(decision, response, policy, certificate, actor_policy)

            st.session_state["context_values"] = deepcopy(decision.context)
            st.session_state["last_payload"] = to_dict(decision)
            st.session_state["last_response"] = to_dict(response)
            st.session_state["last_audit_entry"] = audit_entry
            st.session_state["last_error"] = None
            st.session_state["audit_log"] = [audit_entry, *st.session_state["audit_log"]]
        except Exception as exc:  # pragma: no cover - defensive Streamlit UX path
            st.session_state["last_payload"] = None
            st.session_state["last_response"] = None
            st.session_state["last_audit_entry"] = None
            st.session_state["last_error"] = str(exc)

    if st.session_state["last_error"]:
        st.error(st.session_state["last_error"])
    elif st.session_state["last_response"]:
        st.divider()
        render_outcome(st.session_state["last_response"])

        payload_col, response_col, audit_col = st.columns(3, gap="large")
        with payload_col:
            st.markdown("#### Submitted payload")
            st.json(st.session_state["last_payload"], expanded=False)
        with response_col:
            st.markdown("#### Validation response")
            st.json(st.session_state["last_response"], expanded=False)
        with audit_col:
            st.markdown("#### Latest audit event")
            st.json(st.session_state["last_audit_entry"], expanded=False)

    st.divider()
    render_audit_log(st.session_state["audit_log"])


if __name__ == "__main__":
    main()
