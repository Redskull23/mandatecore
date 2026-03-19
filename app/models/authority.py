from typing import List
from pydantic import BaseModel

class AuthorityCertificate(BaseModel):
    actor_id: str
    actor_role: str
    permitted_actions: List[str]
    max_amount: float
    is_active: bool
    can_override: bool
    delegation_chain_valid: bool
    policy_anchor: str
