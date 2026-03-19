from app.models.authority import AuthorityCertificate

class AuthorityRegistry:
    def __init__(self) -> None:
        self.certificates = {
            "ai_agent_1": AuthorityCertificate(
                actor_id="ai_agent_1",
                actor_role="ai_agent",
                is_active=True,
                delegation_chain_valid=True,
                policy_anchor="demo-authority-registry",
            ),
            "fraud_analyst_1": AuthorityCertificate(
                actor_id="fraud_analyst_1",
                actor_role="fraud_analyst",
                is_active=True,
                delegation_chain_valid=True,
                policy_anchor="demo-authority-registry",
            ),
            "payments_supervisor_1": AuthorityCertificate(
                actor_id="payments_supervisor_1",
                actor_role="payments_supervisor",
                is_active=True,
                delegation_chain_valid=True,
                policy_anchor="demo-authority-registry",
            ),
            "fraud_manager_1": AuthorityCertificate(
                actor_id="fraud_manager_1",
                actor_role="fraud_manager",
                is_active=True,
                delegation_chain_valid=True,
                policy_anchor="demo-authority-registry",
            ),
            "underwriting_analyst_1": AuthorityCertificate(
                actor_id="underwriting_analyst_1",
                actor_role="underwriting_analyst",
                is_active=True,
                delegation_chain_valid=True,
                policy_anchor="demo-authority-registry",
            ),
            "credit_manager_1": AuthorityCertificate(
                actor_id="credit_manager_1",
                actor_role="credit_manager",
                is_active=True,
                delegation_chain_valid=True,
                policy_anchor="demo-authority-registry",
            ),
            "kyc_analyst_1": AuthorityCertificate(
                actor_id="kyc_analyst_1",
                actor_role="kyc_analyst",
                is_active=True,
                delegation_chain_valid=True,
                policy_anchor="demo-authority-registry",
            ),
            "aml_manager_1": AuthorityCertificate(
                actor_id="aml_manager_1",
                actor_role="aml_manager",
                is_active=True,
                delegation_chain_valid=True,
                policy_anchor="demo-authority-registry",
            ),
            "suspended_agent": AuthorityCertificate(
                actor_id="suspended_agent",
                actor_role="ai_agent",
                is_active=False,
                delegation_chain_valid=False,
                policy_anchor="demo-authority-registry",
            ),
            "delegation_gap_analyst": AuthorityCertificate(
                actor_id="delegation_gap_analyst",
                actor_role="fraud_analyst",
                is_active=True,
                delegation_chain_valid=False,
                policy_anchor="demo-authority-registry",
            ),
        }

    def get_certificate(self, actor_id: str):
        return self.certificates.get(actor_id)
