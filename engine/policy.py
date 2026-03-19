from dataclasses import dataclass

@dataclass
class PolicyConfig:
    min_evidence_score: float = 0.75
    escalate_risk_threshold: float = 0.70
    refuse_risk_threshold: float = 0.92

class PolicyEngine:
    def __init__(self) -> None:
        self.config = PolicyConfig()

    def get_config(self, action: str, business_unit: str) -> PolicyConfig:
        # Future state: action-specific, BU-specific, jurisdiction-specific policy resolution
        return self.config
