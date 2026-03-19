from app.models.authority import AuthorityCertificate

class AuthorityRegistry:
    def __init__(self) -> None:
        self.certificates = {
            "ai_wire_agent": AuthorityCertificate(
                actor_id="ai_wire_agent",
                actor_role="ai_agent",
                permitted_actions=["approve_wire", "flag_wire_review"],
                max_amount=10000.0,
                is_active=True,
                can_override=False,
                delegation_chain_valid=True,
                policy_anchor="policy-wire-v1",
            ),
            "fraud_analyst_1": AuthorityCertificate(
                actor_id="fraud_analyst_1",
                actor_role="analyst",
                permitted_actions=["release_fraud_hold", "flag_wire_review", "approve_wire"],
                max_amount=25000.0,
                is_active=True,
                can_override=True,
                delegation_chain_valid=True,
                policy_anchor="policy-fraud-v2",
            ),
            "suspended_agent": AuthorityCertificate(
                actor_id="suspended_agent",
                actor_role="ai_agent",
                permitted_actions=["approve_wire"],
                max_amount=5000.0,
                is_active=False,
                can_override=False,
                delegation_chain_valid=False,
                policy_anchor="policy-wire-v1",
            ),
        }

    def get_certificate(self, actor_id: str):
        return self.certificates.get(actor_id)
