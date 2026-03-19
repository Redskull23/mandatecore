from typing import Optional
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
