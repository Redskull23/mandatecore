from fastapi import APIRouter
from app.models.decision import AIDecision
from app.models.outcome import ValidationResponse
from engine.policy import PolicyEngine
from engine.registry import AuthorityRegistry
from engine.validator import MandateCoreValidator

router = APIRouter()

registry = AuthorityRegistry()
policy_engine = PolicyEngine()
validator = MandateCoreValidator(registry, policy_engine)

@router.get("/health")
def health():
    return {"status": "ok", "service": "MandateCore"}

@router.post("/validate", response_model=ValidationResponse)
def validate_decision(decision: AIDecision):
    return validator.validate(decision)
