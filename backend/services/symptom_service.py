from dataclasses import dataclass


@dataclass
class SymptomAssessmentResult:
    score: int
    risk_level: str
    recommendation: str


def assess_symptoms(answers: dict) -> SymptomAssessmentResult:
    """Rule-based eye symptom triage.

    This does not diagnose a disease. It estimates whether the patient should
    seek ophthalmology review based on warning signs and risk factors.
    """
    score = 0

    # Urgent warning signs carry high weight.
    urgent_fields = [
        "sudden_vision_loss",
        "severe_eye_pain",
        "nausea_with_eye_pain",
        "halos_with_pain",
    ]
    for field in urgent_fields:
        if answers.get(field):
            score += 4

    moderate_fields = [
        "blurred_vision",
        "halos_around_lights",
        "eye_redness",
        "headache",
        "high_eye_pressure_history",
    ]
    for field in moderate_fields:
        if answers.get(field):
            score += 2

    risk_factor_fields = [
        "family_history_glaucoma",
        "diabetes",
        "hypertension",
        "age_over_40",
        "uses_steroids",
    ]
    for field in risk_factor_fields:
        if answers.get(field):
            score += 1

    if score >= 8 or answers.get("sudden_vision_loss"):
        return SymptomAssessmentResult(
            score=score,
            risk_level="Urgent Eye Review Recommended",
            recommendation="Your answers include warning signs. Please seek prompt ophthalmology or emergency medical review.",
        )
    if score >= 5:
        return SymptomAssessmentResult(
            score=score,
            risk_level="Ophthalmology Appointment Recommended",
            recommendation="Your answers suggest that an eye doctor visit is recommended soon.",
        )
    if score >= 2:
        return SymptomAssessmentResult(
            score=score,
            risk_level="Routine Eye Check Recommended",
            recommendation="A routine ophthalmology check is recommended, especially if symptoms continue or risk factors are present.",
        )
    return SymptomAssessmentResult(
        score=score,
        risk_level="Low Immediate Concern",
        recommendation="No urgent warning signs were detected from the answers. Routine eye care is still recommended when symptoms appear.",
    )
