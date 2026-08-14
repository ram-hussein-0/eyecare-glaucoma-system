"""Eye-health assessment service.

The public API keeps the historical `assess_symptoms` function name so existing
routes remain stable while the implementation uses the fuzzy assessment engine.
"""

from backend.services.fuzzy_assessment_service import (
    FuzzyAssessmentError,
    FuzzyAssessmentResult,
    assess_eye_health,
)


SymptomAssessmentResult = FuzzyAssessmentResult


def assess_symptoms(answers: dict) -> SymptomAssessmentResult:
    return assess_eye_health(answers)


__all__ = [
    "FuzzyAssessmentError",
    "SymptomAssessmentResult",
    "assess_symptoms",
]
