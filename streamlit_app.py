from __future__ import annotations

from copy import deepcopy
from typing import Any

import streamlit as st

from app.models.decision import AIDecision
from demo.scenarios import scenarios
from engine.policy import PolicyEngine
from engine.registry import AuthorityRegistry
from engine.validator import MandateCoreValidator


def to_dict(model: Any) -> dict[str, Any]:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


@st.cache_resource
def get_runtime() -> tuple[AuthorityRegistry, PolicyEngine, MandateCoreValidator]:
    registry = AuthorityRegistry()
    policy_engine = PolicyEngine()
    validator = MandateCoreValidator(registry, policy_engine)
    return registry, policy_engine, validator


def get_default_payload() -> dict[str, Any]:
    return deepcopy(scenarios[0]["payload"])


def load_payload(payload: dict[str, Any]) -> None:
    for key, value in payload.items():
        if key == "amount":
            st.session_state["amount"] = float(value) if value is not None else 0.0
        else:
            st.session_state[key] = value
    st.session_state["amount_enabled"] = payload.get("amount") is not None
    st.session_state["last_payload"] = None
    st.session_state["last_response"] = None
    st.session_state["last_error"] = None


def initialize_state() -> None:
    payload = get_default_payload()
    defaults = {
        "decision_id": payload["decision_id"],
        "actor_id": payload["actor_id"],
        "actor_role": payload["actor_role"],
        "action": payload["action"],
        "resource": payload["resource"],
        "amount": float(payload["amount"]) if payload["amount"] is not None else 0.0,
        "amount_enabled": payload["amount"] is not None,
        "risk_score": payload["risk_score"],
        "evidence_score": payload["evidence_score"],
        "jurisdiction": payload["jurisdiction"],
        "business_unit": payload["business_unit"],
        "override_requested": payload["override_requested"],
        "last_payload": None,
        "last_response": None,
        "last_error": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def build_decision() -> AIDecision:
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
    )


def render_outcome(response: dict[str, Any]) -> None:
    outcome = response["outcome"]
    st.markdown(
        f"""
        <div class="outcome-card outcome-{outcome}">
            <div class="eyebrow">Validation outcome</div>
            <div class="outcome-value">{outcome}</div>
            <div>Policy anchor: {response.get("policy_anchor") or "None"}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if outcome == "ALLOW":
        st.success("The decision can be executed within the current delegated authority.")
    elif outcome == "ESCALATE":
        st.warning("The decision needs human review or additional validation before execution.")
    else:
        st.error("The decision should not be executed under the current authority and policy rules.")

    st.markdown("#### Reasons")
    for reason in response["reasons"]:
        st.write(f"- {reason}")

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
                radial-gradient(circle at top left, rgba(14, 116, 144, 0.14), transparent 28%),
                radial-gradient(circle at top right, rgba(217, 119, 6, 0.14), transparent 24%),
                linear-gradient(180deg, #f5f7f2 0%, #ffffff 100%);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
        }

        .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        .hero {
            padding: 1.5rem;
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 24px;
            background: rgba(255, 255, 255, 0.82);
            backdrop-filter: blur(12px);
            box-shadow: 0 24px 60px rgba(15, 23, 42, 0.08);
            margin-bottom: 1rem;
        }

        .eyebrow {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #475569;
        }

        .hero-title {
            font-size: 2.2rem;
            font-weight: 700;
            color: #0f172a;
            margin-top: 0.35rem;
        }

        .hero-copy {
            color: #334155;
            margin-top: 0.6rem;
            max-width: 56rem;
        }

        .outcome-card {
            border-radius: 24px;
            padding: 1.35rem 1.5rem;
            color: #ffffff;
            box-shadow: 0 24px 60px rgba(15, 23, 42, 0.16);
            margin-bottom: 1rem;
        }

        .outcome-ALLOW {
            background: linear-gradient(135deg, #0f766e 0%, #14b8a6 100%);
        }

        .outcome-ESCALATE {
            background: linear-gradient(135deg, #b45309 0%, #f59e0b 100%);
        }

        .outcome-REFUSE {
            background: linear-gradient(135deg, #b91c1c 0%, #ef4444 100%);
        }

        .outcome-value {
            font-size: 2rem;
            font-weight: 700;
            margin-top: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    initialize_state()
    registry, policy_engine, validator = get_runtime()
    policy = policy_engine.get_config(st.session_state["action"], st.session_state["business_unit"])
    scenario_lookup = {scenario["name"]: deepcopy(scenario["payload"]) for scenario in scenarios}

    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">Runtime authority validation</div>
            <div class="hero-title">MandateCore Streamlit Workbench</div>
            <div class="hero-copy">
                Explore the same validation logic as the API flow with editable decision inputs,
                demo presets, and live authority context for each actor.
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
        st.subheader("Known actors")
        for actor_id, cert in registry.certificates.items():
            st.markdown(f"**{actor_id}**")
            st.caption(
                f"{cert.actor_role} | max ${cert.max_amount:,.0f} | "
                f"{'active' if cert.is_active else 'inactive'}"
            )

    left_col, right_col = st.columns([1.3, 1], gap="large")

    with left_col:
        st.subheader("Decision input")
        input_col_1, input_col_2 = st.columns(2)

        with input_col_1:
            st.text_input("Decision ID", key="decision_id")
            st.text_input("Actor ID", key="actor_id")
            st.text_input("Actor role", key="actor_role")
            st.text_input("Action", key="action")
            st.text_input("Resource", key="resource")

        with input_col_2:
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
            st.slider(
                "Evidence score",
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                key="evidence_score",
            )
            st.text_input("Jurisdiction", key="jurisdiction")
            st.text_input("Business unit", key="business_unit")
            st.toggle("Override requested", key="override_requested")

        if st.button("Validate decision", type="primary", use_container_width=True):
            try:
                decision = build_decision()
                response = validator.validate(decision)
                st.session_state["last_payload"] = to_dict(decision)
                st.session_state["last_response"] = to_dict(response)
                st.session_state["last_error"] = None
            except Exception as exc:  # pragma: no cover - defensive Streamlit UX path
                st.session_state["last_payload"] = None
                st.session_state["last_response"] = None
                st.session_state["last_error"] = str(exc)

    with right_col:
        st.subheader("Authority context")
        certificate = registry.get_certificate(st.session_state["actor_id"])
        if certificate is None:
            st.warning("No authority certificate is registered for the current actor.")
        else:
            st.json(to_dict(certificate), expanded=False)

        st.subheader("Policy thresholds")
        threshold_col_1, threshold_col_2, threshold_col_3 = st.columns(3)
        threshold_col_1.metric("Min evidence", f"{policy.min_evidence_score:.2f}")
        threshold_col_2.metric("Escalate at", f"{policy.escalate_risk_threshold:.2f}")
        threshold_col_3.metric("Refuse at", f"{policy.refuse_risk_threshold:.2f}")

    if st.session_state["last_error"]:
        st.error(st.session_state["last_error"])
    elif st.session_state["last_response"]:
        st.divider()
        render_outcome(st.session_state["last_response"])

        payload_col, response_col = st.columns(2, gap="large")
        with payload_col:
            st.markdown("#### Submitted payload")
            st.json(st.session_state["last_payload"], expanded=False)
        with response_col:
            st.markdown("#### Raw response")
            st.json(st.session_state["last_response"], expanded=False)


if __name__ == "__main__":
    main()
