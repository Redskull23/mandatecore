class EvidenceEvaluator:
    @staticmethod
    def is_sufficient(evidence_score: float, minimum: float) -> bool:
        return evidence_score >= minimum
