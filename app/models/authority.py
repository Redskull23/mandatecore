from typing import List

from pydantic import BaseModel, Field

class AuthorityCertificate(BaseModel):
    actor_id: str
    actor_role: str
    permitted_actions: List[str] = Field(default_factory=list)
    max_amount: float = 0.0
    is_active: bool
    can_override: bool = False
    delegation_chain_valid: bool
    policy_anchor: str | None = None
