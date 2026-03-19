from typing import Any, Optional

from pydantic import BaseModel, Field

class AIDecision(BaseModel):
    decision_id: str = Field(..., description="Unique decision event ID")
    actor_id: str = Field(..., description="Agent, user, or service account making the recommendation")
    actor_role: str = Field(..., description="Role of the actor, e.g. ai_agent, analyst, supervisor")
    action: str = Field(..., description="Requested action, e.g. approve_wire, increase_credit_limit")
    resource: str = Field(..., description="Target object of the decision")
    amount: Optional[float] = Field(default=None, description="Monetary value if applicable")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score from 0 to 1")
    evidence_score: float = Field(..., ge=0.0, le=1.0, description="Evidence sufficiency from 0 to 1")
    jurisdiction: str = Field(default="US")
    business_unit: str = Field(default="consumer_banking")
    override_requested: bool = Field(default=False)
    review_case_id: Optional[str] = Field(default=None, description="Optional linked review or case reference")
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Policy-specific decision context used for runtime checks and demo audit logging",
    )
