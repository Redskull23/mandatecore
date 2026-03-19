from enum import Enum
from pydantic import BaseModel
from typing import List

class AuthorityOutcome(str, Enum):
    ALLOW = "ALLOW"
    ESCALATE = "ESCALATE"
    REFUSE = "REFUSE"

class ValidationResponse(BaseModel):
    decision_id: str
    outcome: AuthorityOutcome
    reasons: List[str]
    policy_anchor: str | None = None
    policy_id: str | None = None
    policy_version: str | None = None
